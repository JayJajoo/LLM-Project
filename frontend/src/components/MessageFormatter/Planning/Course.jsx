import React from 'react'
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export default function Course({ course }) {
    return (
        <div>
            <Accordion>
                <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="panel1-content"
                    id="panel1-header"
                >
                    <Typography component="div" sx={{ textAlign: 'left', fontWeight: "bold" }}>
                        {course.course_number} - {course.title}<br />
                        Credits: {course.credit_hours}
                    </Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <>
                        <Typography sx={{ textAlign: 'left', textAlign: "justify" }} component="div">Description: {course.description}</Typography><br></br>
                        <Typography sx={{ textAlign: 'left', textAlign: "justify" }} component="div">{course.reason}</Typography><br></br>
                    </>
                </AccordionDetails>
            </Accordion>
        </div>
    );
}
