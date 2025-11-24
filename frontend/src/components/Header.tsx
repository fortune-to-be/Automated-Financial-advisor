import React from 'react'
import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="bg-white shadow">
      <div className="container mx-auto p-4 flex justify-between items-center">
        <Link to="/" className="text-xl font-semibold">Automated Financial Advisor</Link>
        <nav>
          <Link to="/login" className="mr-4 text-sm text-gray-600">Login</Link>
          <Link to="/register" className="text-sm text-gray-600">Register</Link>
        </nav>
      </div>
    </header>
  )
}
