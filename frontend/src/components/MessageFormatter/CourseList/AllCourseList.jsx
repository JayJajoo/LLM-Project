import React from 'react';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CourseList from '../CourseList';
import { theme } from '../../theme';

function AllCourseList({ data }) {
    return (
        <div>
            <Accordion
                sx={{
                    backgroundColor: "rgba(255, 255, 255, 0.05)", // translucent
                    backdropFilter: "blur(12px)",
                    WebkitBackdropFilter: "blur(12px)",
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: "1rem",
                    padding: "0.5rem",
                    maxWidth: theme.componentsMaxWidth,
                    color: "white",
                }}
            >
                <AccordionSummary
                    expandIcon={<ExpandMoreIcon sx={{ color: "white" }} />}
                    aria-controls="panel1-content"
                    id="panel1-header"
                >
                    <Typography
                        sx={{
                            textAlign: 'left',
                            fontWeight: "bolder",
                            fontSize: theme.fontSize,
                            color: "white"
                        }}
                        component="div"
                    >
                        Relevant Courses
                    </Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <>
                        {data.response.matched_courses.map((course, index) => (
                            <React.Fragment key={index}>
                                <CourseList course={course} />
                                <br />
                            </React.Fragment>
                        ))}
                        <Typography
                            sx={{
                                textAlign: "justify",
                                color: "white",
                            }}
                            component="div"
                        >
                            {data.response.reason}
                        </Typography>
                        <br />
                    </>
                </AccordionDetails>
            </Accordion>
        </div>
    );
}

export default AllCourseList;

// import React from 'react';
// import Accordion from '@mui/material/Accordion';
// import AccordionSummary from '@mui/material/AccordionSummary';
// import AccordionDetails from '@mui/material/AccordionDetails';
// import Typography from '@mui/material/Typography';
// import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// import CourseList from '../CourseList';
// import { theme } from '../../theme';

// function AllCourseList({ data }) {
//     return (
//         <div>
//             <Accordion sx={{backgroundColor:theme.relevatCoursesBGColour,maxWidth:theme.componentsMaxWidth}}>
//                 <AccordionSummary
//                     expandIcon={<ExpandMoreIcon />}
//                     aria-controls="panel1-content"
//                     id="panel1-header"
//                 >
//                     <Typography sx={{ textAlign: 'left', fontWeight: "bolder", fontSize: theme.fontSize }} component="div">Relevant Courses</Typography>
//                 </AccordionSummary>
//                 <AccordionDetails>
//                     <>
//                         {
//                             data.response.matched_courses.map((course, index) => (
//                                 <>
//                                     <CourseList course={course} key={index}></CourseList>
//                                     <br></br>
//                                 </>
//                             ))
//                         }
//                         <Typography sx={{ textAlign: 'left', textAlign: "justify" }} component="div">{data.response.reason}</Typography>
//                         <br></br>
//                     </>
//                 </AccordionDetails>
//             </Accordion>
//         </div>
//     )
// }

// export default AllCourseList