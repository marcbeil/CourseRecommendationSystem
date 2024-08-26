import React, {useState} from 'react';
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Box,
    Button,
    Checkbox,
    CircularProgress,
    Container,
    FormControl,
    FormControlLabel,
    FormGroup,
    InputLabel,
    List,
    ListItem,
    ListItemText,
    MenuItem,
    Pagination,
    Select,
    Slider,
    TextField,
    Typography
} from '@mui/material';
import {Chip, Paper, IconButton} from '@mui/material';


import TopicChips from "./TopicChips";
import logo from '../static/logo.svg';
import languagesData from '../static/data/languages.json';
import studyLevelsData from '../static/data/study_levels.json';
import organisationsData from '../static/data/organisations.json';
import axios from 'axios';
import ModuleDetail from "./ModuleDetail";
import SearchPreviousModules from "./SearchPreviosModules";

const CourseRecommender = () => {
    const [studentText, setStudentText] = useState('');
    const [schools, setSchools] = useState([]);  // Updated to hold multiple schools
    const [departments, setDepartments] = useState({});  // Updated to hold departments for each school
    const [studyLevel, setStudyLevel] = useState('');
    const [ectsRange, setEctsRange] = useState([1, 30]);
    const [languages, setLanguages] = useState(languagesData);
    const [topicsOfInterest, setTopicsOfInterest] = useState({});
    const [excludedTopics, setExcludedTopics] = useState({});
    const [previousModules, setPreviousModules] = useState([]);
    const [modules, setModules] = useState([]);
    const [selectedModule, setSelectedModule] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [pageSize, setPageSize] = useState(15);
    const [showFilters, setShowFilters] = useState(false)
    const [loading, setLoading] = useState(false);


    const handleSubmit = async (event) => {
        event.preventDefault();
        try {
            if (!studentText) {
                setShowFilters(true)
                handleRefresh()
            } else {
                const response = await axios.post('http://localhost:8080/start-extraction', {
                    text: studentText
                });

                if (response.data.success) {
                    const filters = response.data.filters || {};  // Ensure filters is at least an empty object

                    // Set all states with corresponding values or default values
                    setStudyLevel(filters.studyLevel || '');
                    setSchools(filters.schools || []);
                    setDepartments(filters.departments || []);
                    setEctsRange([filters.ectsMin || 1, filters.ectsMax || 30])
                    setTopicsOfInterest(filters.topicsOfInterest || {});
                    setExcludedTopics(filters.topicsToExclude || {});
                    setPreviousModules(filters.previousModules || []);
                    setLanguages(filters.languages || []);

                    setShowFilters(true);
                    handleRefresh()
                } else {
                    console.error('Extraction failed:', response.data.message);
                }
            }
        } catch (error) {
            console.error('Error during extraction:', error);
        }
    };

    const handleSchoolChange = (event) => {
        const {
            target: {value},
        } = event;

        const selectedSchools = typeof value === 'string' ? value.split(',') : value;

        // Update departments based on the selected schools
        const newDepartments = {};
        selectedSchools.forEach((school) => {
            newDepartments[school] = departments[school] || organisationsData[school];
        });

        setSchools(selectedSchools);
        setDepartments(newDepartments);
    };


    const handleDepartmentChange = (school, department) => {
        setDepartments((prevDepartments) => {
            const isDepartmentSelected = prevDepartments[school]?.includes(department);

            // Toggle the department selection
            const updatedDepartments = isDepartmentSelected
                ? prevDepartments[school].filter((dep) => dep !== department)
                : [...(prevDepartments[school] || []), department];

            return {
                ...prevDepartments,
                [school]: updatedDepartments,
            };
        });
    };


    const handleStudyLevelChange = (event) => {
        setStudyLevel(event.target.value);
    };

    const handleEctsRangeChange = (event, newValue) => {
        setEctsRange(newValue);
    };

    const handleLanguageChange = (event) => {
        const {value} = event.target;
        setLanguages((prev) => prev.includes(value) ? prev.filter((id) => id !== value) : [...prev, value]);
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

    const handleRefresh = async (page = currentPage) => {
        setLoading(true);  // Start loading
        setSelectedModule(null);
        setModules([]);

        const filters = {
            schools,
            departments: Object.entries(departments).flatMap(([school, depts]) => {
                // Ensure depts is an array before mapping over it
                if (Array.isArray(depts)) {
                    return depts.map(dept => ({school, dept}));
                }
                return [];  // Return an empty array if depts is not valid
            }),
            studyLevel,
            ectsRange,
            languages,
            topicsOfInterest,
            excludedTopics,
            previousModules: previousModules.map((module) => module.id),
            studentText
        };

        const response = await fetchModules(filters, page);  // Pass the page argument to fetchModules
        if (response) {
            setModules(response.modules);
            setSelectedModule(response.modules[0] || null);
            setTotalPages(response.totalPages);
        }
        setLoading(false);  // End loading
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

    return <Container maxWidth="lg" sx={{mt: 4}}>
        <Box display="flex" justifyContent="left" mb={4}>
            <img src={logo} alt="TUM Logo" style={{width: '150px', height: 'auto'}}/>
        </Box>
        <Typography variant="h4" gutterBottom>
            Friendly Course Recommender
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="center" margin="normal" border={1}
             borderColor="grey.300" borderRadius={2} p={2}>
            <Box
                component="form"
                onSubmit={handleSubmit}
                sx={{
                    width: '100%', // Make sure the form takes full width of the container
                }}
            >
                <Typography variant="h5" gutterBottom>
                    Input Your Study Preferences
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                    Please write something about your studies, preferences, and any specific topics you're interested
                    in.
                </Typography>
                <TextField
                    label="Your Study Preferences"
                    variant="outlined"
                    fullWidth
                    multiline
                    rows={4}
                    value={studentText}
                    onChange={(e) => setStudentText(e.target.value)}
                    sx={{mb: 2}}
                />
                <Button type="submit" variant="contained" color="primary">
                    Submit
                </Button>
            </Box>
        </Box>

        {showFilters && <Box paddingY={2}> <Accordion>
            <AccordionSummary>
                Show Filters
            </AccordionSummary>
            <AccordionDetails>
                <Box margin="normal">
                    {/* Filter Section */}
                    <FormControl fullWidth margin="normal" sx={{mb: 2}}>
                        <InputLabel>Schools</InputLabel>
                        <Select
                            multiple
                            value={schools}
                            onChange={handleSchoolChange}
                            renderValue={(selected) => selected.join(', ')}
                        >
                            {Object.keys(organisationsData).map((school) => (<MenuItem key={school} value={school}>
                                <Checkbox checked={schools.indexOf(school) > -1}/>
                                <ListItemText primary={school}/>
                            </MenuItem>))}
                        </Select>
                    </FormControl>

                    {schools.map((school) => (<Box key={school} sx={{mb: 2}}>

                        <Paper variant="outlined" sx={{p: 2, overflow: 'auto', maxHeight: '200px'}}>
                            <InputLabel>{school} - Departments</InputLabel>
                            <Box
                                display="flex"
                                flexWrap="nowrap"
                                overflowX="auto"
                                overflowY="hidden"
                                maxWidth="100%"
                                alignItems="center"
                                gap={1}
                                sx={{
                                    '&::-webkit-scrollbar': {
                                        height: '8px',
                                    },
                                    '&::-webkit-scrollbar-thumb': {
                                        backgroundColor: '#888',
                                        borderRadius: '4px',
                                    },
                                    '&::-webkit-scrollbar-thumb:hover': {
                                        backgroundColor: '#555',
                                    },
                                }}
                            >
                                {organisationsData[school] && organisationsData[school].map((department) => (
                                    <Chip
                                        key={department}
                                        label={department.replace(/^Department\s*/, '')}
                                        onClick={() => handleDepartmentChange(school, department)}
                                        color={departments[school]?.includes(department) ? 'primary' : 'default'}
                                        variant={departments[school]?.includes(department) ? 'filled' : 'outlined'}
                                        sx={{cursor: 'pointer', whiteSpace: 'nowrap'}}
                                    />
                                ))}
                            </Box>
                        </Paper>


                    </Box>))}


                    <FormControl fullWidth margin="normal" sx={{mb: 2}}>
                        <InputLabel>Study Level</InputLabel>
                        <Select value={studyLevel} onChange={handleStudyLevelChange}>
                            {studyLevelsData.map((level) => (<MenuItem key={level} value={level}>
                                {level}
                            </MenuItem>))}
                        </Select>
                    </FormControl>
                    <Box my={2} sx={{mb: 4}}>
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
                    <FormControl component="fieldset" fullWidth margin="normal" sx={{mb: 2}}>
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
                    <Box sx={{mb: 2}}>
                        <TopicChips
                            topics={topicsOfInterest}
                            setTopics={setTopicsOfInterest}
                            type="interest"
                            fetchTopicMappings={fetchTopicMappings}
                        />
                    </Box>
                    <Box sx={{mb: 2}}>
                        <TopicChips
                            topics={excludedTopics}
                            setTopics={setExcludedTopics}
                            type="excluded"
                            fetchTopicMappings={fetchTopicMappings}
                        />
                    </Box>
                    <Box sx={{mb: 2}}>
                        <SearchPreviousModules
                            previousModules={previousModules}
                            setPreviousModules={setPreviousModules}
                        />
                    </Box>
                    <Button
                        variant="contained"
                        color="primary"
                        fullWidth
                        sx={{mt: 2}}
                        onClick={() => handleRefresh(currentPage)}
                    >
                        Refresh
                    </Button>
                </Box>
            </AccordionDetails>
        </Accordion></Box>}
        {loading && <Box display="flex" justifyContent="center" mt={4}>
            <CircularProgress/>
        </Box>}

        {showFilters && (<Box display="flex" flexDirection="column" height="100%">
                <Box
                    display="flex"
                    justifyContent="space-between"
                    height="80vh"
                    border={1}
                    borderColor="grey.300"
                    borderRadius={2}
                    overflow="hidden"
                >
                    <Box
                        width="30%"
                        pr={2}
                        overflow="auto"
                        sx={{borderRight: '1px solid lightgray'}}
                    >
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
                    <Box
                        width="70%"
                        overflow="auto"
                        p={2}
                        sx={{borderLeft: '1px solid lightgray'}}
                    >
                        {selectedModule && (
                            <ModuleDetail selectedModule={selectedModule} topicsOfInterest={topicsOfInterest}/>)}
                    </Box>
                </Box>
                <Box display="flex" justifyContent="center" mt={2} mb={4}>
                    <Pagination
                        count={totalPages}
                        page={currentPage}
                        onChange={handlePageChange}
                        color="primary"
                    />
                </Box>
            </Box>

        )}
    </Container>;
};

export default CourseRecommender;
