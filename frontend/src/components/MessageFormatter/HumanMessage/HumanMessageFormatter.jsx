import React from 'react';
import { theme } from '../../theme';

function HumanMessageFormatter({ message }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'flex-end',
        padding: '0.5rem',
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.1)', // translucent white
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
          color: 'white',
          maxWidth: '60%',
          padding: '0.75rem 1.25rem',
          borderRadius: '16px',
          wordBreak: 'break-word',
          fontWeight: 'bold',
          fontSize: theme.fontSize,
        }}
      >
        {message}
      </div>
    </div>
  );
}

export default HumanMessageFormatter;


// import React from 'react'
// import { theme } from '../../theme'

// function HumanMessageFormatter({ message }) {
//   return (
//     <div
//       style={{
//         display: 'flex',
//         justifyContent: 'flex-end', 
//         padding: '0.5rem',
//       }}
//     >
//       <div
//         style={{
//           backgroundColor: theme.humanMessageBGColour,
//           maxWidth: '60%',   
//           padding: '0.5rem 1rem',
//           borderRadius: '12px',
//           wordBreak: 'break-word',
//           fontWeight:"bold",
//           fontSize:"1.3rem"
//         }}
//       >
//         {message}
//       </div>
//     </div>
//   )
// }

// export default HumanMessageFormatter
