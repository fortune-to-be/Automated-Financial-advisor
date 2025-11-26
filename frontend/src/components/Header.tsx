import React from 'react'
import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="bg-white shadow">
      <div className="container mx-auto p-4 flex justify-between items-center">
        <Link to="/" className="text-xl font-semibold">Automated Financial Advisor</Link>
        <nav>
          <Link to="/dashboard" className="mr-4 text-sm text-gray-600">Dashboard</Link>
          <Link to="/transactions" className="mr-4 text-sm text-gray-600">Transactions</Link>
          <Link to="/budgets" className="mr-4 text-sm text-gray-600">Budgets</Link>
          <Link to="/goals" className="mr-4 text-sm text-gray-600">Goals</Link>
          <Link to="/recommendations" className="mr-4 text-sm text-gray-600">Recommendations</Link>
          <Link to="/admin/rules" className="text-sm text-gray-600">Admin</Link>
        </nav>
      </div>
    </header>
  )
}
