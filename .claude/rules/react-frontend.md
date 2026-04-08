---
description: React 前端开发规范 (hpc-ui)
globs: "hpc-ui/**/*.{ts,tsx}"
alwaysApply: false
---

# React 前端规范

技术栈：React 18 + TypeScript 5 + Vite + Ant Design + TanStack Query + Zustand

## 铁律

- 组件用函数式 + TypeScript Props 接口，不用 class component
- 数据获取统一用 TanStack Query，不在 useEffect 里直接 fetch
- 全局状态用 Zustand store，不用 Context 传递频繁变更的数据
- 表单用 Ant Design Form，不自己管理表单状态
- 避免嵌套三元运算符，超过 2 个条件用 early return 或 switch
- 组件文件不超过 200 行，超出拆分子组件
- API 类型定义集中管理，不在组件内定义 `any`

## 反面示例

```tsx
// ❌ 在 useEffect 里直接 fetch
useEffect(() => {
  fetch('/api/data').then(r => r.json()).then(setData)
}, [])
// ✅ 用 TanStack Query
const { data } = useQuery({ queryKey: ['data'], queryFn: fetchData })

// ❌ 嵌套三元
{a ? <A /> : b ? <B /> : c ? <C /> : <D />}
// ✅ early return 或 map
const Component = () => {
  if (a) return <A />
  if (b) return <B />
  return <C />
}

// ❌ 用 Context 传递高频变更的状态（每次变更重渲染整棵树）
<FrequentContext.Provider value={count}>
  <HeavyTree />
</FrequentContext.Provider>
// ✅ 用 Zustand（组件只订阅自己需要的 slice）
const count = useAppStore(s => s.count)

// ❌ 自己管表单状态
const [name, setName] = useState('')
const [email, setEmail] = useState('')
const [phone, setPhone] = useState('')
// ✅ 用 Ant Design Form
const [form] = Form.useForm()
```
