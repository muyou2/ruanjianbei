import hashlib
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from .config import get_settings
from .repositories import list_chunks


TOKEN_RE = re.compile(r"[\u4e00-\u9fff]|[A-Za-z_][A-Za-z0-9_+#.-]*")


def extract_text(path: Path, suffix: str) -> str:
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    raise ValueError("仅支持 txt、md、pdf 文件")


def split_text(text: str, title: str, chunk_size: int = 850, overlap: int = 120) -> list[dict[str, Any]]:
    cleaned = re.sub(r"\r\n?", "\n", text).strip()
    if not cleaned:
        return []
    sections = re.split(r"(?m)(?=^#{1,4}\s+|^第[一二三四五六七八九十\d]+[章节])", cleaned)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        while len(section) > chunk_size:
            cut = section.rfind("\n", 0, chunk_size)
            cut = cut if cut > chunk_size // 2 else chunk_size
            chunks.append(section[:cut].strip())
            section = section[max(0, cut - overlap):].strip()
        if section:
            chunks.append(section)
    return [
        {
            "id": hashlib.sha1(f"{title}:{i}:{chunk}".encode("utf-8")).hexdigest()[:20],
            "title": title,
            "content": chunk,
            "position": i,
        }
        for i, chunk in enumerate(chunks)
    ]


def hashing_vector(text: str, dimensions: int = 384) -> list[float]:
    vector = [0.0] * dimensions
    counts = Counter(token.lower() for token in TOKEN_RE.findall(text))
    for token, count in counts.items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest, "big") % dimensions
        sign = 1.0 if digest[0] % 2 == 0 else -1.0
        vector[index] += sign * (1.0 + math.log(count))
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class KnowledgeStore:
    def __init__(self) -> None:
        self.collection = None
        self.embedding_model = None
        self.backend = "local-hashing"
        self.mode_label = "Hashing MVP 检索"
        self.embedding_error = None
        settings = get_settings()
        if settings.embedding_provider.lower() != "hashing":
            try:
                from sentence_transformers import SentenceTransformer

                self.embedding_model = SentenceTransformer(
                    settings.embedding_model,
                    device=settings.embedding_device,
                    local_files_only=True,
                )
                self.backend = "chroma-semantic"
                self.mode_label = "语义向量检索"
            except Exception as error:
                self.embedding_error = f"{type(error).__name__}: {str(error)[:160]}"
        try:
            import chromadb
            from chromadb.config import Settings

            client = chromadb.PersistentClient(
                path=str(settings.chroma_dir),
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = client.get_or_create_collection(
                "python_course_semantic" if self.embedding_model else "python_course_hashing",
                metadata={"hnsw:space": "cosine"},
            )
            if not self.embedding_model:
                self.backend = "chroma-hashing"
        except Exception:
            self.collection = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.embedding_model:
            vectors = self.embedding_model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return vectors.tolist()
        return [hashing_vector(text) for text in texts]

    def upsert(self, document_id: int, chunks: list[dict[str, Any]]) -> None:
        if not self.collection or not chunks:
            return
        self.collection.upsert(
            ids=[c["id"] for c in chunks],
            documents=[c["content"] for c in chunks],
            embeddings=self.embed([c["content"] for c in chunks]),
            metadatas=[
                {"document_id": document_id, "title": c["title"], "position": c["position"]}
                for c in chunks
            ],
        )

    def delete_document(self, document_id: int) -> None:
        if self.collection:
            try:
                self.collection.delete(where={"document_id": document_id})
            except Exception:
                pass

    def search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        if self.collection and self.collection.count() > 0:
            result = self.collection.query(
                query_embeddings=self.embed([query]),
                n_results=min(top_k, self.collection.count()),
                include=["documents", "metadatas", "distances"],
            )
            items = []
            for chunk_id, content, metadata, distance in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
                result["distances"][0],
            ):
                items.append(
                    {
                        "chunk_id": chunk_id,
                        "document_id": metadata.get("document_id"),
                        "title": metadata.get("title", "课程资料"),
                        "content": content,
                        "score": round(max(0.0, 1.0 - float(distance)), 4),
                        "retrieval_backend": self.backend,
                        "retrieval_mode": self.mode_label,
                    }
                )
            return items

        query_vector = hashing_vector(query)
        scored = []
        for chunk in list_chunks():
            score = cosine(query_vector, hashing_vector(chunk["content"]))
            scored.append(
                {
                    "chunk_id": chunk["id"],
                    "document_id": chunk["document_id"],
                    "title": chunk["title"],
                    "content": chunk["content"],
                    "score": round(max(0.0, score), 4),
                    "retrieval_backend": self.backend,
                    "retrieval_mode": self.mode_label,
                }
            )
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]

    def ensure_index(self) -> None:
        chunks = list_chunks()
        if self.collection and self.collection.count() == len(chunks):
            return
        grouped: dict[int, list[dict[str, Any]]] = {}
        for chunk in chunks:
            grouped.setdefault(int(chunk["document_id"]), []).append(chunk)
        for document_id, items in grouped.items():
            self.upsert(document_id, items)

    def status(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "mode": self.mode_label,
            "embedding_model": (
                get_settings().embedding_model if self.embedding_model else None
            ),
            "fallback_reason": self.embedding_error,
        }


knowledge_store = KnowledgeStore()
