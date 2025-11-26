import React, { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend, ResponsiveContainer } from 'recharts'
import { api } from '../services/api'
import RecommendationCard from '../components/RecommendationCard'
import { toast } from 'react-toastify'

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null)
  const [forecast, setForecast] = useState<any>(null)
  const [recommendations, setRecommendations] = useState<any[]>([])

  useEffect(() => {
    fetchSummary()
    fetchForecast()
    fetchRecommendations()
  }, [])

  async function fetchSummary() {
    try {
      const resp = await api.get('/api/reports/summary')
      setSummary(resp.data.data || resp.data)
    } catch (e: any) {
      console.error(e)
      toast.error('Failed to load summary')
    }
  }

  async function fetchForecast() {
    try {
      const resp = await api.get('/api/planner/cashflow-forecast?months=3')
      setForecast(resp.data)
    } catch (e: any) {
      console.error(e)
      toast.error('Failed to load forecast')
    }
  }

  async function fetchRecommendations() {
    try {
      const resp = await api.post('/api/planner/recommend-budgets', { months: 3 })
      const recs = resp.data?.recommended_budgets || resp.data || []
      setRecommendations(recs.slice(0, 3))
    } catch (e: any) {
      console.error(e)
      toast.error('Failed to load recommendations')
    }
  }

  const pieData = summary ? Object.entries(summary.by_category || {}).map(([name, value]) => ({ name, value })) : []

  const lineData = forecast ? (forecast.monthly_forecasts || []).map((m: any) => ({ month: m.period, net: m.net_cashflow })) : []

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Dashboard</h1>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="col-span-1 bg-white p-4 rounded shadow">
          <h3 className="text-lg font-medium">Net Worth</h3>
          <div className="text-3xl mt-2">
            {summary ? ((summary.total_income || 0) - (summary.total_expense || 0)).toFixed(2) : '—'}
          </div>
          <div className="text-sm text-gray-500">Income - Expense (period)</div>
        </div>

        <div className="md:col-span-2 bg-white p-4 rounded shadow">
          <h3 className="text-lg font-medium">Cashflow Preview (3 months)</h3>
          <div style={{ width: '100%', height: 200 }}>
            <ResponsiveContainer>
              <LineChart data={lineData}>
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="net" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-span-1 bg-white p-4 rounded shadow">
          <h3 className="text-lg font-medium">Spending by Category</h3>
          <div style={{ width: '100%', height: 220 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
                  {pieData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={["#3b82f6", "#60a5fa", "#93c5fd", "#c7d2fe"][index % 4]} />
                  ))}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="md:col-span-3 bg-white p-4 rounded shadow">
          <h3 className="text-lg font-medium mb-2">Top Recommendations</h3>
          <div className="grid md:grid-cols-3 gap-3">
            {recommendations.map((r, i) => (
              <RecommendationCard key={i} rec={r} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
