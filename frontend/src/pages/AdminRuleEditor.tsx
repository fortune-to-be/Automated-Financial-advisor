import React, { useEffect, useState } from 'react'
import AceEditor from 'react-ace'
import 'ace-builds/src-noconflict/mode-json'
import 'ace-builds/src-noconflict/theme-github'
import { api } from '../services/api'
import { toast } from 'react-toastify'

export default function AdminRuleEditor() {
  const [isAdmin, setIsAdmin] = useState(false)
  const [value, setValue] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // check profile for admin role (demo: role in profile)
    api.get('/api/auth/profile').then(r => {
      const data = r.data || {}
      setIsAdmin(data.role === 'admin' || data.is_admin === true)
    }).catch(() => setIsAdmin(false))
  }, [])

  async function validate() {
    try {
      setLoading(true)
      const parsed = JSON.parse(value)
      const resp = await api.post('/api/admin/rules/validate', parsed)
      toast.success('Validation result: ' + (resp.data?.message || 'OK'))
    } catch (e: any) {
      console.error(e)
      toast.error('Validation failed: ' + (e?.response?.data?.error || e.message || String(e)))
    } finally {
      setLoading(false)
    }
  }

  if (!isAdmin) return <div className="text-gray-600">Admin access required to edit rules.</div>

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Admin Rule Editor</h1>
      <div>
        <AceEditor
          mode="json"
          theme="github"
          name="admin_rule_editor"
          onChange={(v) => setValue(v)}
          value={value}
          width="100%"
          height="400px"
          setOptions={{ useWorker: false }}
        />
      </div>
      <div className="mt-3">
        <button className="bg-blue-600 text-white px-3 py-1 rounded" onClick={validate} disabled={loading}>Validate</button>
      </div>
    </div>
  )
}
