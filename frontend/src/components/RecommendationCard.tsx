import React from 'react';

type RecommendationCardProps = {
  title?: string;
  amount?: number;
  onApply?: () => void;
};

const RecommendationCard: React.FC<RecommendationCardProps> = ({ title = 'Recommendation', amount = 0, onApply }) => {
  return (
    <div data-testid="recommendation-card" style={{border: '1px solid #ddd', padding: 12, borderRadius: 6}}>
      <h4>{title}</h4>
      <div>{amount.toFixed(2)}</div>
      <button onClick={onApply} data-testid="apply-btn">Apply</button>
    </div>
  );
};

export default RecommendationCard;
