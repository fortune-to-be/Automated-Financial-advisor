import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import { toast } from 'react-toastify'
import GoalForm from '../components/GoalForm'

export default function Goals() {
  const [goals, setGoals] = useState<any[]>([])
  const [editing, setEditing] = useState<any | null>(null)

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const resp = await api.get('/api/goals')
      const data = resp.data?.data || resp.data
      setGoals(data.items || data || [])
    } catch (e) {
      console.error(e)
      toast.error('Failed to load goals')
    }
  }

  async function compute(goalId: number) {
    try {
      const resp = await api.get(`/api/planner/goal-schedule/${goalId}`)
      const data = resp.data
      toast.info(`Monthly required: $${Number(data.monthly_required || 0).toFixed(2)} — Feasible: ${data.is_feasible}`)
    } catch (e) {
      console.error(e)
      toast.error('Failed to compute goal schedule')
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold">Goals</h1>
        <button className="bg-blue-600 text-white px-3 py-1 rounded" onClick={() => setEditing({})}>New Goal</button>
      </div>

      {editing && <div className="mb-4"><GoalForm goal={editing} onSaved={() => { setEditing(null); load() }} /></div>}

      <div className="grid gap-3">
        {goals.map(g => (
          <div key={g.id} className="p-3 bg-white rounded shadow flex justify-between items-center">
            <div>
              <div className="font-medium">{g.name}</div>
              <div className="text-sm text-gray-600">Target: ${Number(g.target_amount).toFixed(2)} — Due: {g.target_date?.split?.('T')?.[0]}</div>
            </div>
            <div className="space-x-2">
              <button className="text-sm text-blue-600" onClick={() => { setEditing(g) }}>Edit</button>
              <button className="text-sm text-green-600" onClick={() => compute(g.id)}>Compute</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
