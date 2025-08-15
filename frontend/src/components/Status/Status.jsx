import React, { useEffect } from 'react'
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import CircularProgress from '@mui/material/CircularProgress';


function Status({ status }) {

    return (
        <div>
            <Stack
                direction="row"
                sx={{
                    backgroundColor: "rgba(255, 255, 255, 0.1)", // transparent white
                    padding: "0.6rem 1rem",
                    maxWidth: "20vw",
                    borderRadius: "1rem",
                    backdropFilter: "blur(10px)",
                    WebkitBackdropFilter: "blur(10px)", // for Safari
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    boxShadow: "0 4px 30px rgba(0, 0, 0, 0.1)",
                    color: "white",
                    alignItems: "center",
                }}
            >
                <CircularProgress sx={{ marginRight: "1rem" }} color="inherit" size={24} />
                <Alert
                    icon={false}
                    sx={{
                        background: "transparent",
                        color: "white",
                        fontWeight: 500,
                        padding: 0,
                        boxShadow: "none",
                    }}
                    severity="info"
                >
                    {status}
                </Alert>
            </Stack>
            <br />
            <br />
        </div>

    )
}

export default Status
