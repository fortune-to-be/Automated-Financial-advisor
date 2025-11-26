import React from 'react'

type Props = {
  tx?: any
  onSaved: () => void
}

export default function TransactionForm({ tx, onSaved }: Props) {
  const [form, setForm] = React.useState({
    transaction_date: tx?.transaction_date || '',
    description: tx?.description || '',
    amount: tx?.amount || 0,
    category_id: tx?.category_id || null,
  })

  async function save() {
    const res = await fetch(`/api/transactions/${tx?.id || ''}`, {
      method: tx?.id ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    if (res.ok) onSaved()
    else alert('Save failed')
  }

  return (
    <div className="p-3 bg-white rounded shadow">
      <label className="block">Date</label>
      <input type="date" value={form.transaction_date} onChange={e => setForm({ ...form, transaction_date: e.target.value })} className="border p-1 w-full mb-2" />
      <label className="block">Description</label>
      <input value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} className="border p-1 w-full mb-2" />
      <label className="block">Amount</label>
      <input type="number" value={String(form.amount)} onChange={e => setForm({ ...form, amount: Number(e.target.value) })} className="border p-1 w-full mb-2" />
      <label className="block">Category ID</label>
      <input value={form.category_id || ''} onChange={e => setForm({ ...form, category_id: e.target.value ? Number(e.target.value) : null })} className="border p-1 w-full mb-2" />
      <div className="flex space-x-2">
        <button className="btn btn-primary" onClick={() => save()}>Save</button>
      </div>
    </div>
  )
}
