import React, { useState, useEffect } from 'react';
import { TextField, Stack, Button } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import { theme } from '../theme';


export default function QueryComponent({ isFormFilled, setQuery, setSubmit, submit }) {
  const [input, setInput] = useState("");

  // Update query as input changes
  const handleInputChange = (e) => {
    setInput(e.target.value);
    setQuery(e.target.value);
  };

  // Clear input when submit is true
  useEffect(() => {
    if (submit) {
      setInput("");
      setSubmit(false); // Reset submit flag if you only want to clear once
    }
  }, [submit, setSubmit]);

  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <TextField
        sx={{
          backgroundColor: theme.queryComponentBGColour,
          borderRadius: "3rem",
          "& .MuiOutlinedInput-root": {
            color:"#ffffff",
            borderRadius: "3rem",
            padding: "1rem 3rem", // adjust internal spacing instead
          },
        }}
        disabled={!isFormFilled}
        fullWidth
        placeholder={!isFormFilled ? "Please enter the required details first" : "Type your message..."}
        variant="outlined"
        size="small"
        multiline
        minRows={3}
        maxRows={4}
        value={input}
        onChange={handleInputChange}
      />
      <Button
        disabled={!isFormFilled}
        variant="contained"
        endIcon={<SendIcon />}
        sx={{ whiteSpace: 'nowrap' , borderRadius:"2rem"}}
        onClick={() => setSubmit(true)}
      >
        Send
      </Button>
    </Stack>
  );
}
