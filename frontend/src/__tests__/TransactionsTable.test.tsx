import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import TransactionsTable from '../components/TransactionsTable'

describe('TransactionsTable', () => {
  it('renders rows for transactions', () => {
    const data = [
      { id: 1, date: '2025-11-01', description: 'Coffee', amount: 3.5 },
      { id: 2, date: '2025-11-02', description: 'Groceries', amount: 45.2 },
    ]
    render(<TransactionsTable transactions={data} />)

    expect(screen.getByTestId('transactions-table')).toBeInTheDocument()
    expect(screen.getByText('Coffee')).toBeInTheDocument()
    expect(screen.getByText('45.20')).toBeInTheDocument()
  })
})
