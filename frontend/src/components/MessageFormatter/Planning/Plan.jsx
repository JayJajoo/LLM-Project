// import React from 'react';
// import Accordion from '@mui/material/Accordion';
// import AccordionSummary from '@mui/material/AccordionSummary';
// import AccordionDetails from '@mui/material/AccordionDetails';
// import Typography from '@mui/material/Typography';
// import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// import Semester from './Semester';
// import { theme } from '../../theme';

// export default function Plan({ plan }) {
//   return (
//     <div>
//       <Accordion sx={{backgroundColor:theme.planBoxBGColour,
//         maxWidth:theme.componentsMaxWidth,}}>
//         <AccordionSummary
//           expandIcon={<ExpandMoreIcon />}
//           aria-controls="panel1-content"
//           id="panel1-header"
//         >
//           <Typography sx={{ textAlign: 'left', fontWeight:"bolder",fontSize:theme.fontSize}} component="div">Plan {plan.plan_number}</Typography>
//         </AccordionSummary>
//         <AccordionDetails>
//           <>
//             <Typography  sx={{ textAlign: 'left', fontWeight:"bold"}} component="div">Total Semesters: {plan.total_semesters}</Typography><br />
//             <Typography sx={{ textAlign: 'left', fontWeight:"bold"}} component="div">Total Credits: {plan.total_credits}</Typography><br />
//             {
//               plan.semester_schedule.map((semester, index) => (
//                 <>
//                 <Semester key={index} semester={semester} />
//                 <br></br>
//                 </>
//               ))
//             }
//             <Typography sx={{ textAlign: 'left',textAlign: "justify",color:theme.reasoningColour,fontSize:"1.1rem"}} component="div">{plan.reason_behind_planning}</Typography>
//             <br></br>
//           </>
//         </AccordionDetails>
//       </Accordion>
//     </div>
//   );
// }

import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Semester from './Semester';
import { theme } from '../../theme';

export default function Plan({ plan }) {
  return (
    <div>
      <Accordion
        sx={{
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
          borderRadius: '1rem',
          padding: '0.5rem',
          maxWidth: theme.componentsMaxWidth,
          color: 'white',
        }}
      >
        <AccordionSummary
          expandIcon={<ExpandMoreIcon sx={{ color: 'white' }} />}
          aria-controls="panel1-content"
          id="panel1-header"
        >
          <Typography
            sx={{
              textAlign: 'left',
              fontWeight: 'bolder',
              fontSize: theme.fontSize,
              color: 'white',
            }}
            component="div"
          >
            Plan {plan.plan_number}
          </Typography>
        </AccordionSummary>

        <AccordionDetails>
          <>
            <Typography sx={{ textAlign: 'left', fontWeight: 'bold', color: 'white' }} component="div">
              Total Semesters: {plan.total_semesters}
            </Typography>
            <br />
            <Typography sx={{ textAlign: 'left', fontWeight: 'bold', color: 'white' }} component="div">
              Total Credits: {plan.total_credits}
            </Typography>
            <br />

            {plan.semester_schedule.map((semester, index) => (
              <React.Fragment key={index}>
                <Semester semester={semester} />
                <br />
              </React.Fragment>
            ))}

            <Typography
              sx={{
                textAlign: 'justify',
                color: theme.reasoningColour || 'white',
                fontSize: theme.fontSize,
                // marginTop: '0.5rem',
              }}
              dangerouslySetInnerHTML={{ __html: plan.reason_behind_planning }}
              component="div"
            >
              {/* {plan.reason_behind_planning} */}
            </Typography>
            <br />
          </>
        </AccordionDetails>
      </Accordion>
    </div>
  );
}

