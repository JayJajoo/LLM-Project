import React, { useEffect } from 'react';
import { Box } from '@mui/material';

import QueryComponent from './QueryComponent';
import HumanMessageFormatter from '../MessageFormatter/HumanMessage/HumanMessageFormatter';

import AllPlanFormatter from '../MessageFormatter/Planning/AllPlanFormatter';
import ShortTermPlan from '../MessageFormatter/ShortTerm/ShortTermPlan';
import Greeting from '../MessageFormatter/Greeting/Greeting';
import AllCourseList from '../MessageFormatter/CourseList/AllCourseList';
import { theme } from '../theme';
import Status from '../Status/Status';


export default function ChatContainer({ status, isFormFilled, setQuery, setSubmit, submit, messages }) {

  // useEffect(()=>{
  //   if (messages){
  //     console.log(messages)
  //   }
  // },[messages])

  return (
    <Box
      sx={{
        height: '96vh',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box sx={{ flex: 1, overflowY: 'auto', scrollbarWidth: "none", padding: 2 }}>
        {
          messages.map((message, index) => {
            if (message) {
              if (message[0] === "User") {
                return <><HumanMessageFormatter key={index} message={message[2]} /><br /></>;
              } else {
                if (message[1] === "Planning" || message[1] === "Rescheduling") {
                  return <><AllPlanFormatter key={index} plans={message[2]} /><br /></>;
                }
                else if (message[1] === "ShortTermPlan") {
                  return <><ShortTermPlan plan={message[2]}></ShortTermPlan><br /></>
                }
                else if (message[1] === "Greeting") {
                  return <><Greeting message={message[2]}></Greeting><br /></>
                }
                else if (message[1] === "CourseExtractor") {
                  return <><AllCourseList data={message[2]}></AllCourseList><br /></>
                }
                else {
                  return null
                }
              }
            }
            return null;
          })
        }
      </Box>
      {status && <div style={{marginLeft:"auto",marginRight:"auto"}}> 
        <Status status={status}/>
        </div>
      }

      <Box sx={{ paddingTop: "3vh", marginTop: "1rem" }}>
        <QueryComponent isFormFilled={isFormFilled} setQuery={setQuery} submit={submit} setSubmit={setSubmit}></QueryComponent>
      </Box>
    </Box>
  );
}
