import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function CourseList({ course }) {
  return (
    <div
      style={{
        padding: '1rem',
        borderRadius: '16px',
        background: 'rgba(44, 200, 143, 1)', // soft bluish tint
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
        marginBottom: '1rem',
      }}
    >
      <Accordion
        sx={{
          backgroundColor: 'rgba(35, 45, 42, 0.05)',
          borderRadius: '12px',
          boxShadow: 'none',
          '&:before': {
            display: 'none',
          },
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon sx={{ color: '#333' }} />}
          aria-controls="panel1-content"
          id="panel1-header"
        >
          <Typography
            component="div"
            sx={{
              textAlign: 'left',
              fontWeight: 'bold',
              fontSize: '0.95rem',
              color: '#222',
            }}
          >
            {course.course_number} - {course.title}
            <br />
            Credits: {course.credit_hours}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography sx={{ textAlign: 'justify', fontSize: '0.9rem', mb: 1 }}>
            <strong>College:</strong> {course.college}
          </Typography>
          <Typography sx={{ textAlign: 'justify', fontSize: '0.9rem', mb: 1 }}>
            <strong>Department:</strong> {course.department}
          </Typography>
          <Typography sx={{ textAlign: 'justify', fontSize: '0.9rem', mb: 1 }}>
            <strong>Description:</strong> {course.description}
          </Typography>
          <Typography sx={{ textAlign: 'justify', fontSize: '0.9rem' }}>
            <strong>Prerequisites:</strong> {course.prerequisites}
          </Typography>
        </AccordionDetails>
      </Accordion>
    </div>
  );
}


// import React from 'react'
// import Accordion from '@mui/material/Accordion';
// import AccordionSummary from '@mui/material/AccordionSummary';
// import AccordionDetails from '@mui/material/AccordionDetails';
// import Typography from '@mui/material/Typography';
// import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

// export default function CourseList({ course }) {
//     return (
//         <div>
//             <Accordion>
//                 <AccordionSummary
//                     expandIcon={<ExpandMoreIcon />}
//                     aria-controls="panel1-content"
//                     id="panel1-header"
//                 >
//                     <Typography component="div" sx={{ textAlign: 'left', fontWeight: "bold", fontSize:"0.9rem"}}>
//                         {course.course_number} - {course.title}<br />
//                         Credits: {course.credit_hours}
//                     </Typography>
//                 </AccordionSummary>
//                 <AccordionDetails>
//                     <>
//                         <Typography sx={{ textAlign: 'left', textAlign: "justify", fontSize:"0.8rem" }} component="div"><strong>College:</strong> {course.college}</Typography>
//                         <Typography sx={{ textAlign: 'left', textAlign: "justify" , fontSize:"0.8rem"}} component="div"><strong>Department:</strong> {course.department}</Typography>
//                         <Typography sx={{ textAlign: 'left', textAlign: "justify" , fontSize:"0.8rem"}} component="div"><strong>Description:</strong> {course.description}</Typography>
//                         <Typography sx={{ textAlign: 'left', textAlign: "justify" , fontSize:"0.8rem"}} component="div"><strong>Prerequisites:</strong> {course.prerequisites}</Typography>
//                     </>
//                 </AccordionDetails>
//             </Accordion>
//         </div>
//     );
// }
