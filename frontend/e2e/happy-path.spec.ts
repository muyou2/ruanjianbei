import { expect, test } from '@playwright/test'

test('核心学习闭环可以完成', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '今天，和一组 AI 教练一起学习' })).toBeVisible()

  await page.getByRole('link', { name: '学生画像' }).click()
  await page.locator('textarea').fill('我是计算机专业大二学生，函数和 Pandas 不熟，希望通过图解、代码和项目练习学习。')
  await page.getByRole('button', { name: /生成学习画像/ }).click()
  await expect(page.getByText('我的画像卡片')).toBeVisible()
  await expect(page.getByText('计算机专业', { exact: true })).toBeVisible()

  await page.getByRole('link', { name: '课程知识库' }).click()
  await expect(page.getByText(/已入库文档/)).toBeVisible()
  await page.getByRole('button', { name: /检索/ }).click()
  await expect(page.getByText(/片段 1/)).toBeVisible()

  await page.getByRole('link', { name: '资源生成' }).click()
  await page.getByRole('button', { name: /启动智能体协作/ }).click()
  await expect(page.getByText('资源包生成完成')).toBeVisible({ timeout: 30_000 })
  await expect(page.getByText(/个性化学习路径/)).toBeVisible()

  await page.getByRole('link', { name: '智能答疑' }).click()
  await page.getByRole('button', { name: /发送/ }).click()
  await expect(page.getByText(/参考 1/)).toBeVisible({ timeout: 30_000 })

  await page.getByRole('link', { name: '学习评估' }).click()
  await expect(page.getByText(/第 1 题/)).toBeVisible()
})
