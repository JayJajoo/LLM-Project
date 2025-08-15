import React, { useState, useEffect } from 'react';
import DropDown from './DropDown';
import MultiSelectDropDown from './MultiSelectDropDown';
import courses from "../data/courses.json";
import colleges from "../data/colleges.json";
import departments from "../data/departments.json";
import { numplans, totalcredits,maxminpersem } from '../data/creditsData';
import Typography from '@mui/material/Typography';
import { theme } from '../theme';


function SideBar({ setIsFormFilled, setFormData }) {
    const [selectedCollege, setSelectedCollege] = useState(null);
    const [selectedDepartment, setSelectedDepartment] = useState(null);
    const [selectedCoreCourses, setSelectedCoreCourses] = useState([]);
    const [selectedTotalCredits, setSelectedTotalCredits] = useState(null);
    const [selectedMinCredits, setSelectedMinCredits] = useState(null);
    const [selectedMaxCredits, setSelectedMaxCredits] = useState(null);
    const [selectedNumPlans,setSelectedNumPlans] = useState(null)

    useEffect(() => {
        const isFilled = Boolean(
            selectedCollege &&
            selectedDepartment &&
            selectedCoreCourses.length > 0 &&
            selectedTotalCredits &&
            selectedMinCredits &&
            selectedMaxCredits &&
            selectedNumPlans
        );
        setIsFormFilled(isFilled);

        if (isFilled) {

            const college = selectedCollege.value;
            const department = selectedDepartment.value;

            const totalcreds = parseInt(selectedTotalCredits.value);
            const mincreds = parseInt(selectedMinCredits.value);
            const maxcreds = parseInt(selectedMaxCredits.value);

            const courses = selectedCoreCourses.map(course => course.value);

            const numPlans = parseInt(selectedNumPlans.value);

            // console.log(numPlans)

            setFormData({
                "college":college,
                "department":department,
                "max_creds_per_sem":maxcreds,
                "min_creds_per_sem":mincreds,
                "core_course_numbers":courses,
                "max_credits":totalcreds,
                "max_number_of_plans":numPlans
            })

        }

    }, [
        selectedCollege,
        selectedDepartment,
        selectedCoreCourses,
        selectedTotalCredits,
        selectedMinCredits,
        selectedMaxCredits,
        selectedNumPlans
    ]);

    return (
        <div style={{padding:"1rem"}}>
            <Typography sx={{ textAlign: 'left',fontSize:"1.5rem",color: theme.slectionBGColour ,fontWeight:"bolder"}} component="div">Enter Your Details</Typography><br></br>

            <DropDown label={"College"} data={colleges} onChange={setSelectedCollege} />
            <br />
            <DropDown label={"Department"} data={departments}  onChange={setSelectedDepartment} />
            <br />
            <MultiSelectDropDown label={"Core Courses"} data={courses}  onChange={setSelectedCoreCourses} />
            <br />
            <DropDown label={"Total Credits to Complete"} data={totalcredits} onChange={setSelectedTotalCredits} />
            <br />
            <DropDown label={"Minimum Credits Per Semester"} data={maxminpersem}  onChange={setSelectedMinCredits} />
            <br />
            <DropDown label={"Maximum Credits Per Semester"} data={maxminpersem}  onChange={setSelectedMaxCredits} />
            <br />
            <DropDown label={"Plans to Generate"} data={numplans} onChange={setSelectedNumPlans} />

        </div>
    );
}

export default SideBar;
