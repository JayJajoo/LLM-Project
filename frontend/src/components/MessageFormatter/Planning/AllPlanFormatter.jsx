import React from 'react';
import Plan from './Plan';

function AllPlanFormatter({ plans }) {
  return (
    <div>
      {
        plans.map((plan, index) => (
            <>
          <Plan key={index} plan={plan} /><br/>
          </>
        ))
      }
    </div>
  );
}

export default AllPlanFormatter;
