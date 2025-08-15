import React, { useEffect, useState } from 'react';
import { styled } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import SideBar from './MainPage/SideBar';
import ChatContainer from './MainPage/ChatContainer';
import axios from "axios"
import { v4 as uuidv4 } from 'uuid';
import { SERVER_URL } from './Routes/route';
import { theme } from './theme';


const Item = styled(Paper)(({ theme }) => ({
  backgroundColor: '#fff',
  ...theme.typography.body2,
  padding: theme.spacing(1),
  textAlign: 'center',
  color: (theme.vars ?? theme).palette.text.secondary,
  ...theme.applyStyles('dark', {
    backgroundColor: '#1A2027',
  }),
}));

export default function MainPage() {

  const [isFormFilled, setIsFormFilled] = useState(false)
  const [formData, setFormData] = useState(null)
  const [query, setQuery] = useState("")
  const [submit, setSubmit] = useState(false)
  const [messages, setMessages] = useState([])
  const [status, setStatus] = useState(null)

  useEffect(() => {
    if (isFormFilled) {
      setIsFormFilled(true)
    }
  }, [isFormFilled])

  useEffect(() => {
    if (String(query).trim() != null) {
      setQuery(query)
    }
    else {
      setQuery("")
    }
    setSubmit(false)
  }, [query])

  // useEffect(() => {
  //   if (status != null) {
  //     console.log(status)
  //   }
  // }, [status])

  async function get_ai_response(formdata) {
    const controller = new AbortController();
    const decoder = new TextDecoder();

    const response = await fetch(SERVER_URL, {
      method: "POST",
      signal: controller.signal,
      body: JSON.stringify(formdata),
      headers: {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
      }
    });

    const reader = response.body.getReader();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // Process full lines
      const lines = buffer.split("\n\n");
      buffer = lines.pop(); // Save incomplete line back to buffer

      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const data = line.replace("data:", "").trim();

        if (data.startsWith("[FINAL_OUTPUT]")) {
          try {
            const jsonStr = data.replace("[FINAL_OUTPUT]", "").trim();
            const newMessage = JSON.parse(jsonStr);

            setMessages(newMessage)
          } catch (err) {
            console.error("Failed to parse FINAL_OUTPUT:", err);
          }
        } 
        else {
          // setStatus(status)
          setStatus((prevStatus) => {
            if (prevStatus !== data) {
              return data;
            }
            return prevStatus;
          });
        }
      }
    }

    setStatus(null)
  }

  // async function get_ai_response(formdata) {
  //   // let data = await axios.post(SERVER_URL, formdata, {
  //   //   "Content-Type": "application/json",
  //   // })
  //   // setMessages(data.data.data)

  //   const controller = new AbortController()
  //   const decoder = new TextDecoder()

  //   const response = await fetch(SERVER_URL, {
  //     method: "POST",
  //     signal: controller.signal,
  //     body: formdata,
  //     headers: {
  //       "Accept": "text/event-stream"
  //     }
  //   })

  //   const reader = response.body.getReader()

  //   while (true) {
  //     const { done, value } = await reader.read()
  //     if (done) {
  //       break
  //     }

  //     const chunk = decoder.decode(value, { stream: true })

  //     if (chunk.includes("[FINAL_OUTPUT]")) {
  //       const parts = chunk.split("[FINAL_OUTPUT]")
  //       const messages = JSON.parse(parts[parts.length - 1].trim())
  //       setMessages((prevMsgs) => {
  //         if (prevMsgs.length > 0 && JSON.stringify(prevMsgs) != JSON.stringify(messages)) {
  //           return messages
  //         }
  //         else {
  //           return prevMsgs
  //         }
  //       })
  //     }
  //     else {
  //       const parts = chunk.split("data:")
  //       const status = String(parts[parts.length - 1].trim())
  //       setStatus((prevStatus) => {
  //         if (prevStatus != null && prevStatus != status) {
  //           return status
  //         }
  //         else {
  //           return prevStatus
  //         }
  //       })
  //     }

  //   }
  // }

  function getOrCreateThreadId() {
    let threadId = sessionStorage.getItem("threadId");

    if (!threadId) {
      const sessionId = uuidv4();
      threadId = `${sessionId}-${uuidv4()}`;
      sessionStorage.setItem("threadId", threadId);
    }
    return threadId;
  }

  useEffect(() => {
    if (submit && String(query).trim()) {
      messages.push(["User", "Query", query])
      setMessages(messages)
      setQuery("")
      const thread_id = getOrCreateThreadId()
      const formdata = { "query": query, "thread_id": thread_id, ...formData }
      
      get_ai_response(formdata)
      setSubmit(false)
    }
  }, [submit])

  return (
    <Box sx={{ flexGrow: 1, backgroundColor: theme.mainBGColour }}>
      <Grid container spacing={0} >
        <Grid size={2} style={{ backgroundColor: theme.sideBarBGColour }}>
          <Item style={{ backgroundColor: theme.sideBarBGColour }}>
            <div style={{ "height": theme.mainHeight, backgroundColor: theme.sideBarBGColour, overflowY: "scroll", scrollbarWidth: "none", msOverflowStyle: "none" }}>
              <SideBar setIsFormFilled={setIsFormFilled} setFormData={setFormData}></SideBar>
            </div></Item>
        </Grid>
        <Grid size={10}>
          <Item style={{ backgroundColor: theme.messageContainerBGColour }}>
            <div style={{ "height": theme.mainHeight }}>
              <ChatContainer status={status} messages={messages} isFormFilled={isFormFilled} setQuery={setQuery} submit={submit} setSubmit={setSubmit}></ChatContainer>
            </div></Item>
        </Grid>
        {submit}
      </Grid>
    </Box>
  );
}
