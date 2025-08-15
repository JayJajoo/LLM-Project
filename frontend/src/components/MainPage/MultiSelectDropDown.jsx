import React from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import { theme } from '../theme';

export default function MultiSelectDropDown({ label, data, onChange }) {
  return (
    <Autocomplete
      multiple
      id={"tags-outlined"}
      options={data}
      getOptionLabel={(option) =>
        option.misc_data ? `${option.value} - ${option.misc_data}` : String(option.value)
      }
      filterSelectedOptions
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
              color: theme.labelColourAfter,                   // selected chips text color
              backgroundColor: theme.tagColour,          // optional chip background
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
        />
      )}
    />
  );
}
