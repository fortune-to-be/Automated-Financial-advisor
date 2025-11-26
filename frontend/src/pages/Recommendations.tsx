import React, { useEffect, useState } from 'react'
import { api } from '../services/api'
import RecommendationCard from '../components/RecommendationCard'
import { toast } from 'react-toastify'

export default function Recommendations() {
  const [recs, setRecs] = useState<any[]>([])

  useEffect(() => { load() }, [])

  async function load() {
    try {
      const resp = await api.post('/api/planner/recommend-budgets', { months: 3 })
      const data = resp.data || {}
      const list = data.recommended_budgets || []
      setRecs(list)
    } catch (e) {
      console.error(e)
      toast.error('Failed to load recommendations')
    }
  }

  async function apply(rec: any) {
    try {
      // best-effort: call budgets API to create/update budget
      await api.post('/api/budgets', { category_id: rec.category_id, limit_amount: rec.monthly_amount })
      toast.success('Applied recommendation')
      load()
    } catch (e) {
      console.error(e)
      toast.error('Failed to apply recommendation')
    }
  }

  function snooze(idx: number) {
    toast.info('Snoozed')
    setRecs(prev => prev.filter((_, i) => i !== idx))
  }

  function dismiss(idx: number) {
    toast.info('Dismissed')
    setRecs(prev => prev.filter((_, i) => i !== idx))
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold">Recommendations</h1>
      </div>

      <div className="grid md:grid-cols-3 gap-3">
        {recs.map((r, i) => (
          <div key={i} className="p-3 bg-white rounded shadow">
            <RecommendationCard rec={r} />
            <div className="mt-3 flex space-x-2">
              <button className="text-sm text-green-600" onClick={() => apply(r)}>Apply</button>
              <button className="text-sm text-yellow-600" onClick={() => snooze(i)}>Snooze</button>
              <button className="text-sm text-gray-600" onClick={() => dismiss(i)}>Dismiss</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
