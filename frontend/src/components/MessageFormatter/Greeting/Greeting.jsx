import React from 'react';
import { theme } from '../../theme';

function Greeting({ message }) {
  return (
    <div
      style={{
        display: 'flex',
      }}
    >
      <div
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.1)', // glass background
          color: 'white',
          maxWidth: theme.componentsMaxWidth,
          padding: '0.75rem 1.25rem',
          borderRadius: '16px',
          wordBreak: 'break-word',
          fontWeight: 'bold',
          fontSize: theme.fontSize,
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)', // for Safari
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
        }}
      >
        {message}
      </div>
    </div>
  );
}

export default Greeting;


// import React from 'react'
// import { theme } from '../../theme'

// function Greeting({message}) {
//   return (
//     <div
//       style={{
//         display: 'flex', 
//         padding: '0.5rem',
//       }}
//     >
//       <div
//         style={{
//           backgroundColor: theme.humanMessageBGColour,
//           color:"black",
//           maxWidth: theme.componentsMaxWidth,   
//           padding: '0.5rem 1rem',
//           borderRadius: '12px',
//           wordBreak: 'break-word',
//           fontWeight:"bold",
//           fontSize:theme.fontSize
//         }}
//       >
//         {message}
//       </div>
//     </div>
//   )
// }

// export default Greeting