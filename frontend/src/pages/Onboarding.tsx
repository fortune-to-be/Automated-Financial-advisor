import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Onboarding() {
  const [income, setIncome] = useState('')
  const [accounts, setAccounts] = useState('')
  const [bills, setBills] = useState('')
  const nav = useNavigate()

  function submit(e: React.FormEvent) {
    e.preventDefault()
    // For demo, simply navigate to dashboard (not implemented)
    nav('/login')
  }

  return (
    <div className="max-w-2xl mx-auto bg-white rounded shadow p-6 mt-8">
      <h2 className="text-2xl mb-4">Welcome — Onboarding</h2>
      <form onSubmit={submit}>
        <label className="block mb-2">Monthly Income
          <input className="border p-2 w-full" value={income} onChange={e => setIncome(e.target.value)} />
        </label>
        <label className="block mb-2">Accounts (comma separated)
          <input className="border p-2 w-full" value={accounts} onChange={e => setAccounts(e.target.value)} />
        </label>
        <label className="block mb-4">Recurring bills (comma separated)
          <input className="border p-2 w-full" value={bills} onChange={e => setBills(e.target.value)} />
        </label>
        <button className="bg-indigo-600 text-white px-4 py-2 rounded">Finish</button>
      </form>
    </div>
  )
}
