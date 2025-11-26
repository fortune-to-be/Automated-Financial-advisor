import React from 'react'

type Props = {
  onClose: () => void
  onImported: () => void
}

export default function ImportCsvModal({ onClose, onImported }: Props) {
  const [preview, setPreview] = React.useState<any[] | null>(null)
  const [file, setFile] = React.useState<File | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [rowsAccepted, setRowsAccepted] = React.useState<Record<number, boolean>>({})

  async function uploadPreview() {
    if (!file) return
    setLoading(true)
    const form = new FormData()
    form.append('file', file)

    try {
      const res = await fetch('/api/transactions/import/preview', { method: 'POST', body: form })
      if (!res.ok) throw new Error('Preview failed')
      const data = await res.json()
      const items = data.items || data || []
      setPreview(items)
      // default accept all
      const accepted: any = {}
      (items || []).forEach((_: any, i: number) => { accepted[i] = true })
      setRowsAccepted(accepted)
    } catch (err) {
      console.error(err)
      alert('Preview failed')
    } finally {
      setLoading(false)
    }
  }

  async function commitImport() {
    if (!file) return
    setLoading(true)
    try {
      // If preview exists, create a CSV from accepted rows; otherwise upload original file
      let form = new FormData()
      if (preview && preview.length > 0) {
        // Build CSV header from keys of first row
        const keys = Object.keys(preview[0])
        const rows: string[] = []
        rows.push(keys.join(','))
        preview.forEach((r: any, idx: number) => {
          if (!rowsAccepted[idx]) return
          const vals = keys.map(k => {
            const v = r[k]
            if (v === null || v === undefined) return ''
            // escape quotes
            return String(v).replace(/"/g, '""')
          })
          rows.push(vals.join(','))
        })
        const csvContent = rows.join('\n')
        const blob = new Blob([csvContent], { type: 'text/csv' })
        form.append('file', blob, 'import.csv')
      } else {
        form.append('file', file)
      }

      const res = await fetch('/api/transactions/import/commit', { method: 'POST', body: form })
      if (!res.ok) throw new Error('Import failed')
      onImported()
      onClose()
    } catch (err) {
      console.error(err)
      alert('Import failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40">
      <div className="bg-white p-4 rounded w-11/12 max-w-2xl">
        <h3 className="text-lg font-semibold mb-2">Import Transactions CSV</h3>
        <input type="file" accept="text/csv" onChange={e => setFile(e.target.files?.[0] || null)} />
        <div className="mt-3 flex space-x-2">
          <button className="btn btn-primary" onClick={() => uploadPreview()} disabled={loading}>Preview</button>
          <button className="btn" onClick={() => commitImport()} disabled={loading || !preview}>Import</button>
          <button className="btn" onClick={() => onClose()}>Close</button>
        </div>

        {preview && (
          <div className="mt-4 max-h-64 overflow-auto">
            <div className="flex justify-between mb-2">
              <div />
              <div>
                <button className="btn mr-2" onClick={() => { const all: Record<number, boolean> = {}; preview.forEach((_: any, i: number) => all[i] = true); setRowsAccepted(all) }}>Accept All</button>
                <button className="btn" onClick={() => { const none: Record<number, boolean> = {}; preview.forEach((_: any, i: number) => none[i] = false); setRowsAccepted(none) }}>Reject All</button>
              </div>
            </div>
            <table className="min-w-full">
              <thead>
                <tr>
                  <th className="p-1">#</th>
                  <th className="p-1">Date</th>
                  <th className="p-1">Description</th>
                  <th className="p-1">Amount</th>
                  <th className="p-1">Applied Rules</th>
                  <th className="p-1">Action</th>
                </tr>
              </thead>
              <tbody>
                {preview.map((r, idx) => (
                  <tr key={idx} className="border-t">
                    <td className="p-1">{idx + 1}</td>
                    <td className="p-1">{r.transaction_date}</td>
                    <td className="p-1">{r.description}</td>
                    <td className="p-1">{r.amount}</td>
                    <td className="p-1">{JSON.stringify(r.applied_rules || r.rule_trace || [])}</td>
                    <td className="p-1">
                      {rowsAccepted[idx] ? (
                        <button className="text-sm text-red-600" onClick={() => setRowsAccepted(prev => ({ ...prev, [idx]: false }))}>Reject</button>
                      ) : (
                        <button className="text-sm text-green-600" onClick={() => setRowsAccepted(prev => ({ ...prev, [idx]: true }))}>Accept</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
