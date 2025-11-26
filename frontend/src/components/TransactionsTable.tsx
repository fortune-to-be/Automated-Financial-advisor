import React from 'react';

type Transaction = {
  id: number;
  date: string;
  description: string;
  amount: number;
};

type Props = {
  transactions?: Transaction[];
};

const TransactionsTable: React.FC<Props> = ({ transactions = [] }) => {
  return (
    <table data-testid="transactions-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Description</th>
          <th>Amount</th>
        </tr>
      </thead>
      <tbody>
        {transactions.map(t => (
          <tr key={t.id}>
            <td>{t.date}</td>
            <td>{t.description}</td>
            <td>{t.amount.toFixed(2)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default TransactionsTable;
