import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CourseList from '../CourseList';
import { theme } from '../../theme';

function ShortTermPlan({ plan }) {
    return (
        <div>
            <Accordion
                sx={{
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    WebkitBackdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.3)',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
                    borderRadius: '16px',
                    color: 'white',
                    maxWidth: theme.componentsMaxWidth,
                    padding:"0.5rem",
                    mt: 2
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
                            color: 'white'
                        }}
                        component="div"
                    >
                        Suggested Courses
                    </Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <>
                        {plan.content.suggestions.map((course, index) => (
                            <div key={index}>
                                <CourseList course={course} />
                                <br />
                            </div>
                        ))}
                        <Typography
                            sx={{
                                textAlign: 'justify',
                                color: 'rgba(255, 255, 255, 0.9)',
                                fontSize: theme.fontSize,
                                mt: 1
                            }}
                            component="div"
                        >
                            {plan.content.explaination}
                        </Typography>
                        <br />
                    </>
                </AccordionDetails>
            </Accordion>
        </div>
    );
}

export default ShortTermPlan;


// import React from 'react';
// import Accordion from '@mui/material/Accordion';
// import AccordionSummary from '@mui/material/AccordionSummary';
// import AccordionDetails from '@mui/material/AccordionDetails';
// import Typography from '@mui/material/Typography';
// import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// import CourseList from '../CourseList';
// import { theme } from '../../theme';

// function ShortTermPlan({ plan }) {
//     return (
//         <div>
//             <Accordion sx={{backgroundColor:theme.suggestedCourseBGColour,maxWidth:theme.componentsMaxWidth}}>
//                 <AccordionSummary
//                     expandIcon={<ExpandMoreIcon />}
//                     aria-controls="panel1-content"
//                     id="panel1-header"
//                 >
//                     <Typography sx={{ textAlign: 'left', fontWeight: "bolder", fontSize: theme.fontSize }} component="div">Suggested Courses</Typography>
//                 </AccordionSummary>
//                 <AccordionDetails>
//                     <>
//                         {
//                             plan.content.suggestions.map((course, index) => (
//                                 <>
//                                     <CourseList course={course} key={index}></CourseList>
//                                     <br></br>
//                                 </>
//                             ))
//                         }
//                         <Typography sx={{ textAlign: 'left', textAlign: "justify" ,color:theme.reasoningColour,fontSize:"1.1rem"}} component="div">{plan.content.explaination}</Typography>
//                         <br></br>
//                     </>
//                 </AccordionDetails>
//             </Accordion>
//         </div>
//     )
// }

// export default ShortTermPlan