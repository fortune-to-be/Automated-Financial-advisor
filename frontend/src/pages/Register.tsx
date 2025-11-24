import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setAccessToken } from '../services/api'

export default function Register() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const nav = useNavigate()

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const resp = await api.post('/api/auth/register', { email, username, password })
      const { access_token } = resp.data || {}
      if (access_token) {
        setAccessToken(access_token)
        nav('/onboarding')
      } else {
        nav('/onboarding')
      }
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Registration failed')
    }
  }

  return (
    <div className="max-w-md mx-auto bg-white rounded shadow p-6 mt-8">
      <h2 className="text-2xl mb-4">Register</h2>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      <form onSubmit={submit}>
        <label className="block mb-2">Email
          <input className="border p-2 w-full" value={email} onChange={e => setEmail(e.target.value)} />
        </label>
        <label className="block mb-2">Username
          <input className="border p-2 w-full" value={username} onChange={e => setUsername(e.target.value)} />
        </label>
        <label className="block mb-4">Password
          <input type="password" className="border p-2 w-full" value={password} onChange={e => setPassword(e.target.value)} />
        </label>
        <button className="bg-green-600 text-white px-4 py-2 rounded">Register</button>
      </form>
    </div>
  )
}
