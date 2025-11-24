import React from 'react'

type Props = {
  children: React.ReactNode
}

export default function AuthForm({ children }: Props) {
  return (
    <div className="max-w-md mx-auto bg-white rounded shadow p-6 mt-8">{children}</div>
  )
}
