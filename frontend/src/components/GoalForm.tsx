import React, { useState } from 'react'
import { api } from '../services/api'
import { toast } from 'react-toastify'

export default function GoalForm({ goal, onSaved }: any) {
  const [form, setForm] = useState({
    name: goal?.name || '',
    target_amount: goal?.target_amount || '',
    target_date: goal?.target_date ? goal.target_date.split('T')[0] : ''
  })

  async function save() {
    try {
      if (goal && goal.id) {
        await api.put(`/api/goals/${goal.id}`, form)
      } else {
        await api.post('/api/goals', form)
      }
      toast.success('Goal saved')
      onSaved()
    } catch (e) {
      console.error(e)
      toast.error('Failed to save goal')
    }
  }

  return (
    <div className="p-3 bg-white rounded shadow">
      <label className="block">Name</label>
      <input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="border p-1 w-full mb-2" />
      <label className="block">Target Amount</label>
      <input type="number" value={String(form.target_amount)} onChange={e => setForm({ ...form, target_amount: Number(e.target.value) })} className="border p-1 w-full mb-2" />
      <label className="block">Target Date</label>
      <input type="date" value={form.target_date} onChange={e => setForm({ ...form, target_date: e.target.value })} className="border p-1 w-full mb-2" />
      <div className="flex space-x-2">
        <button className="btn btn-primary" onClick={save}>Save</button>
      </div>
    </div>
  )
}
