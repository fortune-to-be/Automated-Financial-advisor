import React, { Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Register from './pages/Register'
import Onboarding from './pages/Onboarding'
import Header from './components/Header'
import Dashboard from './pages/Dashboard'
import { ToastContainer } from 'react-toastify'

const Transactions = React.lazy(() => import('./pages/Transactions'))
const Budgets = React.lazy(() => import('./pages/Budgets'))
const Goals = React.lazy(() => import('./pages/Goals'))
const Recommendations = React.lazy(() => import('./pages/Recommendations'))
const AdminRuleEditor = React.lazy(() => import('./pages/AdminRuleEditor'))

export default function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="container mx-auto p-4">
        <Suspense fallback={<div>Loading...</div>}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/budgets" element={<Budgets />} />
            <Route path="/goals" element={<Goals />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/admin/rules" element={<AdminRuleEditor />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </main>
      <ToastContainer />
    </div>
  )
}
