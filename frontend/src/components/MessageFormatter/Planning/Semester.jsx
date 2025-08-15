import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Course from './Course';
import { theme } from '../../theme';

export default function Semester({ semester }) {
    return (
        <div>
            <Accordion
                sx={{
                    backgroundColor: 'rgba(230, 88, 111, 1)', // translucent yellow
                    backdropFilter: 'blur(10px)',
                    WebkitBackdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    boxShadow: '0 4px 30px rgba(0, 0, 0, 0.1)',
                    borderRadius: '16px',
                    maxWidth: theme.componentsMaxWidth,
                }}
            >
                <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="panel1-content"
                    id="panel1-header"
                >
                    <Typography component="div" sx={{ textAlign: 'left', fontWeight: "bold" }}>
                        Semester {semester.semester}
                    </Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <>
                        <Typography sx={{ textAlign: 'left', fontWeight: "bold" }} component="div">
                            Semester Total Credits: {semester.total_credits}
                        </Typography>
                        <br />
                        {
                            semester.courses.map((course, index) => (
                                <React.Fragment key={index}>
                                    <Course course={course} />
                                    <br />
                                </React.Fragment>
                            ))
                        }
                    </>
                </AccordionDetails>
            </Accordion>
        </div>
    );
}


// import React from 'react';
// import Accordion from '@mui/material/Accordion';
// import AccordionSummary from '@mui/material/AccordionSummary';
// import AccordionDetails from '@mui/material/AccordionDetails';
// import Typography from '@mui/material/Typography';
// import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// import Course from './Course';
// import { theme } from '../../theme';

// export default function Semester({ semester }) {
//     return (
//         <div>
//             <Accordion sx={{backgroundColor:theme.semesterBoxBGColour}}>
//                 <AccordionSummary
//                     expandIcon={<ExpandMoreIcon />}
//                     aria-controls="panel1-content"
//                     id="panel1-header"
//                 >
//                     <Typography component="div" sx={{ textAlign: 'left', fontWeight:"bold"}}>Semester {semester.semester}</Typography>
//                 </AccordionSummary>
//                 <AccordionDetails>
//                     <>
//                         <Typography sx={{ textAlign: 'left', fontWeight:"bold"}} component="div">Semester Total Credits: {semester.total_credits}</Typography>
//                         <br></br>
//                         {
//                             semester.courses.map((course, index) => (
//                                 <>
//                                     <Course key={index} course={course} />
//                                     <br></br>
//                                 </>
//                             ))
//                         }
//                     </>
//                 </AccordionDetails>
//             </Accordion>
//         </div>
//     );
// }