import React, {useEffect, useState} from 'react';
import {
    Box,
    Button,
    Container,
    FormControl,
    Checkbox,
    FormControlLabel,
    FormGroup,
    InputLabel,
    MenuItem,
    Select,
    Slider,
    Typography,
    List,
    ListItem,
    ListItemText,
    Pagination
} from '@mui/material';

import TopicChips from "./TopicChips";
import logo from '../static/logo.svg';
import schoolsData from '../static/data/schools.json';
import departmentsData from '../static/data/departments.json';
import languagesData from '../static/data/languages.json';
import studyLevelsData from '../static/data/study_levels.json';
import axios from 'axios';
import {useLocation} from "react-router-dom";
import ModuleDetail from "./ModuleDetail";
import SearchPreviousModules from "./SearchPreviosModules";

const CourseRecommender = () => {
    const location = useLocation();  // Get the passed state
    const filtersFromState = location.state || {};  // Use an empty object if no state is passed
    const studentText = filtersFromState.studentText
    const [school, setSchool] = useState(filtersFromState.school || '');
    const [departments, setDepartments] = useState(filtersFromState.departments || []);
    const [studyLevel, setStudyLevel] = useState(filtersFromState.studyLevel || '');
    const [ectsRange, setEctsRange] = useState([filtersFromState.ectsMin || 1, filtersFromState.ectsMax || 30]);
    const [languages, setLanguage] = useState(filtersFromState.languages || languagesData);
    const [topicsOfInterest, setTopicsOfInterest] = useState(filtersFromState.topicsOfInterest || {});
    const [excludedTopics, setExcludedTopics] = useState(filtersFromState.topicsToExclude || {});
    const [previousModules, setPreviousModules] = useState([]);
    const [modules, setModules] = useState([]);
    const [selectedModule, setSelectedModule] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [pageSize, setPageSize] = useState(10);

    useEffect(() => {
        // Automatically fetch modules if filters are passed from the previous page
        if (Object.keys(filtersFromState).length > 0) {
            handleRefresh(currentPage);  // Use the current page
        }
    }, []); // Only run once on component mount


    const handleSchoolChange = (event) => {
        console.log(studentText)
        const selectedSchool = event.target.value;
        setSchool(selectedSchool);

        // Set all departments of the selected school by default
        const departmentsForSchool = departmentsData[selectedSchool].map((department) => department.id);
        setDepartments(departmentsForSchool);
    };

    const handleDepartmentChange = (event) => {
        const {value} = event.target;
        setDepartments((prev) => prev.includes(value) ? prev.filter((id) => id !== value) : [...prev, value]);
    };

    const handleStudyLevelChange = (event) => {
        setStudyLevel(event.target.value);
    };

    const handleEctsRangeChange = (event, newValue) => {
        setEctsRange(newValue);
    };

    const handleLanguageChange = (event) => {
        const {value} = event.target;
        setLanguage((prev) => prev.includes(value) ? prev.filter((id) => id !== value) : [...prev, value]);
    };

    const fetchTopicMappings = async (topic) => {
        try {
            const response = await axios.get('http://localhost:8080/map-topic', {
                params: {
                    topic
                },
            });
            return response.data.topicMappings || [];  // Ensure an array is returned
        } catch (error) {
            console.error('Error fetching topic mapping:', error);
            return [];  // Return an empty array in case of error
        }
    };

    const handleRefresh = async (page = currentPage) => {  // Accept a page argument, defaulting to currentPage
        const filters = {
            school,
            departments,
            studyLevel,
            ectsRange,
            languages,
            topicsOfInterest,
            excludedTopics,
            previousModules: previousModules.map((module) => module.id),
        };

        const response = await fetchModules(filters, page);  // Pass the page argument to fetchModules
        if (response) {
            setModules(response.modules);
            setTotalPages(response.totalPages);
        }
    };

    const fetchModules = async (filters, page) => {  // Accept page as an argument
        try {
            console.log(filters)
            // Flatten the topicsOfInterest mappings into a single array
            const flattenedTopicsOfInterest = Object.values(filters.topicsOfInterest).flat();
            const flattenedExcludedTopics = Object.values(filters.excludedTopics).flat();

            // Include the flattened topics in the filters object
            const params = {
                ...filters, topicsOfInterest: flattenedTopicsOfInterest,  // Send the flattened topics to the backend
                excludedTopics: flattenedExcludedTopics,  // Send the flattened excluded topics to the backend
                page: page,  // Use the passed page
                size: pageSize,
            };
            const response = await axios.get('http://localhost:8080/modules', {
                params: params,
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching modules:', error);
            // Handle error appropriately
        }
    };

    const handlePageChange = (event, value) => {
        setCurrentPage(value);
        handleRefresh(value); // Refresh data with the new page number
    };

    const handleModuleClick = (module) => {
        setSelectedModule(module);
    };

    return (<Container maxWidth="lg" sx={{mt: 4}}>
        <Box display="flex" justifyContent="left" mb={4}>
            <img src={logo} alt="TUM Logo" style={{width: '150px', height: 'auto'}}/>
        </Box>
        <Typography variant="h4" gutterBottom>
            Friendly Course Recommender
        </Typography>
        <Box marginY={4}>
            <Typography variant="h6" gutterBottom>
                Original Input
            </Typography>
            <Typography gutterBottom>
                {studentText}
            </Typography>
        </Box>
        <Box margin="normal">
            <FormControl fullWidth margin="normal">
                <InputLabel>School</InputLabel>
                <Select value={school} onChange={handleSchoolChange}>
                    {schoolsData.map((school) => (<MenuItem key={school.id} value={school.name}>
                        {school.name}
                    </MenuItem>))}
                </Select>
            </FormControl>
            {school && <FormControl component="fieldset" fullWidth margin="normal">
                <Typography component="legend">Department</Typography>
                <FormGroup>
                    {departmentsData[school] && departmentsData[school].map((department) => (<FormControlLabel
                        key={department.id}
                        control={<Checkbox
                            checked={departments.includes(department.id)}
                            onChange={handleDepartmentChange}
                            value={department.id}
                        />}
                        label={department.name}
                    />))}
                </FormGroup>
            </FormControl>}
            <FormControl fullWidth margin="normal">
                <InputLabel>Study Level</InputLabel>
                <Select value={studyLevel} onChange={handleStudyLevelChange}>
                    {studyLevelsData.map((level) => (<MenuItem key={level} value={level}>
                        {level}
                    </MenuItem>))}
                </Select>
            </FormControl>
            <Box my={2}>
                <Typography gutterBottom>ECTS Range</Typography>
                <Slider
                    value={ectsRange}
                    onChange={handleEctsRangeChange}
                    valueLabelDisplay="auto"
                    disableSwap={true}
                    min={1}
                    max={30}
                />
            </Box>
            <FormControl component="fieldset" fullWidth margin="normal">
                <Typography component="legend">Language Preference</Typography>
                <FormGroup row>
                    {languagesData.map((lang) => (<FormControlLabel
                        key={lang}
                        control={<Checkbox
                            checked={languages.includes(lang)}
                            onChange={handleLanguageChange}
                            value={lang}
                        />}
                        label={lang}
                    />))}
                </FormGroup>
            </FormControl>
            <TopicChips
                topics={topicsOfInterest}
                setTopics={setTopicsOfInterest}
                type="interest"
                fetchTopicMappings={fetchTopicMappings}
            />
            <TopicChips
                topics={excludedTopics}
                setTopics={setExcludedTopics}
                type="excluded"
                fetchTopicMappings={fetchTopicMappings}
            />
            <SearchPreviousModules previousModules={previousModules} setPreviousModules={setPreviousModules}/>
            <Button variant="contained" color="primary" fullWidth style={{marginTop: '20px'}}
                    onClick={() => handleRefresh(currentPage)}>
                Refresh
            </Button>
        </Box>
        <Box display="flex" justifyContent="space-between">
            <Box width="30%" pr={2}>
                <Box mt={4}>
                    <List>
                        {modules.map((module) => (<ListItem
                            button
                            key={module.id}
                            onClick={() => handleModuleClick(module)}
                            selected={selectedModule?.id === module.id} // Highlight if this is the selected module
                            sx={{
                                backgroundColor: selectedModule?.id === module.id ? 'rgba(0, 123, 255, 0.1)' : 'inherit', // Light blue background for selected item
                                '&:hover': {
                                    backgroundColor: 'rgba(0, 123, 255, 0.2)', // Slightly darker blue on hover
                                },
                            }}
                        >
                            <ListItemText primary={`${module.id} - ${module.title}`}/>
                        </ListItem>))}
                    </List>
                </Box>
            </Box>
            <Box width="70%" ml={4} margin="normal">
                {selectedModule && (
                    <ModuleDetail selectedModule={selectedModule} topicsOfInterest={topicsOfInterest}/>)}
            </Box>
        </Box>
        <Box display="flex" justifyContent="center" mt={4}>
            <Pagination count={totalPages} page={currentPage} onChange={handlePageChange} color="primary"/>
        </Box>
    </Container>);
};

export default CourseRecommender;
