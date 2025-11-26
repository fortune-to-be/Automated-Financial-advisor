import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import { toast } from 'react-toastify'

function BudgetRow({ b, onSaved }: any) {
  const [editing, setEditing] = useState(false)
  const [limit, setLimit] = useState(b.limit_amount || '')

  async function save() {
    try {
      await api.put(`/api/budgets/${b.id}`, { limit_amount: Number(limit) })
      toast.success('Budget updated')
      setEditing(false)
      onSaved()
    } catch (e) {
      console.error(e)
      toast.error('Failed to update budget')
    }
  }

  const spent = b.spent || 0
  const percent = b.limit_amount ? Math.min(100, (spent / b.limit_amount) * 100) : 0

  return (
    <div className="p-3 bg-white rounded shadow mb-3">
      <div className="flex justify-between items-center">
        <div>
          <div className="font-medium">{b.category_name || 'Uncategorized'}</div>
          <div className="text-sm text-gray-500">Limit: ${b.limit_amount?.toFixed?.(2) || b.limit_amount || 0}</div>
        </div>
        <div className="w-1/3">
          <div className="h-3 bg-gray-200 rounded">
            <div style={{ width: `${percent}%` }} className={`h-3 rounded ${percent > 90 ? 'bg-red-500' : 'bg-green-500'}`}></div>
          </div>
          <div className="text-sm text-gray-600 mt-1">Spent: ${Number(spent).toFixed(2)} ({percent.toFixed(0)}%)</div>
        </div>
      </div>

      <div className="mt-3">
        {editing ? (
          <div className="flex items-center space-x-2">
            <input value={limit} onChange={e => setLimit(e.target.value)} className="border p-1" />
            <button className="text-sm text-green-600" onClick={save}>Save</button>
            <button className="text-sm text-gray-600" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        ) : (
          <button className="text-sm text-blue-600" onClick={() => setEditing(true)}>Edit</button>
        )}
      </div>
    </div>
  )
}

export default function Budgets() {
  const [budgets, setBudgets] = useState<any[]>([])

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const resp = await api.get('/api/budgets')
      const data = resp.data?.data || resp.data
      setBudgets(data.items || data || [])
    } catch (e) {
      console.error(e)
      toast.error('Failed to load budgets')
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold">Budgets</h1>
      </div>

      {budgets.map(b => (
        <BudgetRow key={b.id} b={b} onSaved={load} />
      ))}

      {budgets.length === 0 && (
        <div className="text-gray-500">No budgets found.</div>
      )}
    </div>
  )
}
