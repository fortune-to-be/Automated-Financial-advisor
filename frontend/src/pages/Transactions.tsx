import React, { useEffect, useState } from 'react'
import TransactionsTable from '../components/TransactionsTable'
import ImportCsvModal from '../components/ImportCsvModal'
import { api } from '../services/api'
import { toast } from 'react-toastify'

export default function Transactions() {
  const [transactions, setTransactions] = useState<any[]>([])
  const [showImport, setShowImport] = useState(false)

  useEffect(() => {
    loadTransactions()
  }, [])

  async function loadTransactions() {
    try {
      const resp = await api.get('/api/transactions/')
      const data = resp.data?.data || resp.data
      setTransactions(data.items || data || [])
    } catch (e: any) {
      console.error(e)
      toast.error('Failed to load transactions')
    }
  }

  async function onCategoryChange(txId: number, newCategoryId: number | null) {
    // optimistic update
    const prev = transactions.slice()
    const idx = transactions.findIndex(t => t.id === txId)
    if (idx === -1) return
    const updated = { ...transactions[idx], category_id: newCategoryId }
    const next = transactions.slice()
    next[idx] = updated
    setTransactions(next)

    try {
      await api.put(`/api/transactions/${txId}`, { category_id: newCategoryId })
      toast.success('Category updated')
    } catch (e: any) {
      setTransactions(prev)
      toast.error('Failed to update category')
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold">Transactions</h1>
        <div>
          <button className="bg-blue-600 text-white px-3 py-1 rounded mr-2" onClick={() => setShowImport(true)}>Import CSV</button>
        </div>
      </div>

      <TransactionsTable transactions={transactions} onCategoryChange={onCategoryChange} onReload={loadTransactions} />

      {showImport && <ImportCsvModal onClose={() => { setShowImport(false); loadTransactions() }} />}
    </div>
  )
}
