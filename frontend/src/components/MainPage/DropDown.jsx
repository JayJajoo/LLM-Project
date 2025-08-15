import * as React from 'react';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import CircularProgress from '@mui/material/CircularProgress';
import { theme } from '../theme';


function sleep(duration) {
  return new Promise((resolve) => setTimeout(resolve, duration));
}

export default function DropDown({ label, data, onChange }) {
  const [open, setOpen] = React.useState(false);
  const [options, setOptions] = React.useState([]);
  const [loading, setLoading] = React.useState(false);

  const handleOpen = () => {
    setOpen(true);
    (async () => {
      setLoading(true);
      setOptions([...data]);
      setLoading(false);
    })();
  };

  const handleClose = () => {
    setOpen(false);
    setOptions([]);
  };

  return (
    <Autocomplete
      sx={{ width: "100%" }}
      open={open}
      onOpen={handleOpen}
      onClose={handleClose}
      isOptionEqualToValue={(option, value) => option.value === value.value}
      getOptionLabel={(option) => String(option.value)}
      options={options}
      loading={loading}
      onChange={(event, newValue) => onChange(newValue)}
      renderInput={(params) => (
        <TextField
          sx={{
            backgroundColor: theme.sideBarBGColour,
            borderRadius: theme.borderRadius,
            color: theme.labelColourAfter, // Text color

            "& .MuiOutlinedInput-root": {
              color: theme.labelColourAfter, // Input text color
              borderRadius: theme.borderRadius,
              "& fieldset": {
                borderColor: theme.labelColourAfter, // default border
              },
              "&:hover fieldset": {
                borderColor: theme.labelColourAfter, // on hover
              },
              "&.Mui-focused fieldset": {
                borderColor: theme.labelColourAfter, // on focus
              },
            },

            "& .MuiInputLabel-root": {
              color: theme.labelColourBefore,
            },
            "& .MuiInputLabel-root.Mui-focused": {
              color: theme.labelColourAfter,
            },

            "& .MuiAutocomplete-tag": {
              color: theme.sideBarBGColour,                  
              backgroundColor: theme.labelColourAfter,      
            },
            "& .MuiAutocomplete-clearIndicator": {
              color: theme.labelColourAfter, 
            },

            "& .MuiAutocomplete-popupIndicator": {
              color: theme.labelColourAfter, 
            },
          }}
          {...params}
          label={label}
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={20} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
    />
  );
}
