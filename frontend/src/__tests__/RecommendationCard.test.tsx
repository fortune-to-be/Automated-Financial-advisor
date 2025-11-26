import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import RecommendationCard from '../components/RecommendationCard'

describe('RecommendationCard', () => {
  it('renders title and amount and handles apply click', () => {
    const onApply = vi.fn()
    render(<RecommendationCard title="Test" amount={12.5} onApply={onApply} />)

    expect(screen.getByTestId('recommendation-card')).toBeInTheDocument()
    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('12.50')).toBeInTheDocument()

    fireEvent.click(screen.getByTestId('apply-btn'))
    expect(onApply).toHaveBeenCalled()
  })
})
