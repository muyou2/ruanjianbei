import { expect, test } from '@playwright/test'

test('高校 Python 个性化学习闭环真实跑通', async ({ page }) => {
  await page.goto('/profile')
  await expect(page.getByText('小林 · 基础薄弱型')).toBeVisible()

  const demoText = '我是计算机专业大二学生，Python 基础一般，函数、Pandas 和数据分析项目不熟，希望通过图解、代码案例和项目练习学习。'
  await page.locator('textarea').fill(demoText)
  await page.getByRole('button', { name: /生成并保存画像/ }).click()
  await expect(page.getByText('自定义学习者的画像')).toBeVisible()
  await expect(page.getByText('计算机专业', { exact: true })).toBeVisible()
  await expect(page.getByText('Pandas', { exact: false })).toBeVisible()

  await page.getByRole('link', { name: '课程知识库' }).click()
  await expect(page.getByText(/MVP Hashing 向量/)).toBeVisible()
  await page.getByRole('button', { name: /检索/ }).click()
  await expect(page.getByText(/片段 1/)).toBeVisible()

  await page.getByRole('link', { name: '资源生成' }).click()
  await page.locator('input').fill('Pandas 数据清洗与分析综合实践')
  await page.getByRole('button', { name: /启动智能体协作/ }).click()
  await expect(page.getByText('资源包生成完成')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText('saved', { exact: true })).toBeVisible()
  await expect(page.getByText(/生成智能体：PlannerAgent/)).toBeVisible()

  await page.getByRole('link', { name: '智能答疑' }).click()
  await page.locator('textarea').fill('Pandas 处理缺失值时为什么不能总是删除整行？')
  await page.getByRole('button', { name: /发送/ }).click()
  await expect(page.getByText(/知识库证据/)).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText(/参考 1/)).toBeVisible()

  await page.getByRole('link', { name: '学习评估' }).click()
  await page.getByLabel('直接删除所有空值').check()
  await page.getByLabel('正确').check()
  const textareas = page.locator('textarea')
  await textareas.nth(0).fill('直接删除即可')
  await textareas.nth(1).fill("df = pd.read_csv('data.csv')")
  await page.getByRole('button', { name: /提交答案/ }).click()
  await expect(page.getByText('画像写回结果')).toBeVisible()
  await expect(page.getByText(/未执行代码/)).toBeVisible()

  await page.getByRole('link', { name: '学习总览' }).click()
  await expect(page.getByText('最近错题与测评证据')).toBeVisible()
  await expect(page.getByText(/最近测评/)).toBeVisible()
})
