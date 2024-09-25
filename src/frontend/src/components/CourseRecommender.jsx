import React, {useEffect, useState} from 'react';
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
    styled,
    Tab,
    Tabs,
    TextField,
    Tooltip,
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
    const [digitalScoreRange, setDigitalScoreRange] = useState([0, 3])
    const [languages, setLanguages] = useState(languagesData);
    const [topicsOfInterest, setTopicsOfInterest] = useState({});
    const [excludedTopics, setExcludedTopics] = useState({});
    const [previousModules, setPreviousModules] = useState([]);
    const [modules, setModules] = useState([]);
    const [modulesRankedByLLM, setModulesRankedByLLM] = useState(null)
    const [selectedTab, setSelectedTab] = useState(0); // 0 for "Modules" tab, 1 for "LLM Modules" tab
    const [selectedModule, setSelectedModule] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [showFilters, setShowFilters] = useState(false)
    const [loading, setLoading] = useState(false);
    const [filtersExpanded, setFiltersExpanded] = useState(false);
    const [loadingRankedModules, setLoadingRankedModules] = useState(false); // New state to track loading ranked modules


// Add this useEffect after your state declarations
    useEffect(() => {
        if (showFilters) {  // Ensure filters are visible
            handleRefresh();
        }
    }, [showFilters]);  // Add all relevant states here

    const handleSubmit = async (event) => {
        event.preventDefault();
        try {
            if (!studentText) {
                setSelectedTab(0)
                setShowFilters(true);
            } else {
                setLoading(true); // Start loading
                setSelectedTab(0)
                setFiltersExpanded(false)
                setShowFilters(false)
                setSelectedModule(null);
                setModules([]);
                setModulesRankedByLLM(null)
                const response = await axios.post('http://localhost:8080/start-extraction', {
                    text: studentText
                });

                if (response.data.success) {
                    const filters = response.data.filters || {}; // Ensure filters is at least an empty object

                    // Set all states with corresponding values or default values
                    setStudyLevel(filters.studyLevel || '');
                    setSchools(filters.schools || []);
                    setDepartments(filters.departments || {});
                    setEctsRange([filters.ectsMin || 1, filters.ectsMax || 30]);
                    setTopicsOfInterest(filters.topicsOfInterest || {});
                    setExcludedTopics(filters.topicsToExclude || {});
                    setPreviousModules(filters.previousModules || []);
                    setLanguages(filters.languages || []);
                    setShowFilters(true);
                } else {
                    console.error('Extraction failed:', response.data.message);
                }
            }
        } catch (error) {
            console.error('Error during extraction:', error);
        } finally {
            setLoading(false); // End loading
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
            const updatedDepartments = isDepartmentSelected ? prevDepartments[school].filter((dep) => dep !== department) : [...(prevDepartments[school] || []), department];

            return {
                ...prevDepartments, [school]: updatedDepartments,
            };
        });
    };

    const handleAccordionChange = () => {
        setFiltersExpanded(!filtersExpanded);
    };

    const handleStudyLevelChange = (event) => {
        setStudyLevel(event.target.value);
    };

    const handleEctsRangeChange = (event, newValue) => {
        setEctsRange(newValue);
    };
    const handleDigitalScoreRange = (event, newValue) => {
        setDigitalScoreRange(newValue);
    };
    const handleLanguageChange = (event) => {
        const {value} = event.target;
        setLanguages((prev) => prev.includes(value) ? prev.filter((id) => id !== value) : [...prev, value]);
    };
    const handleTabChange = (event, newValue) => {
        setSelectedTab(newValue);
        if (newValue === 0) {
            setSelectedModule(modules[0])
        } else {
            setSelectedModule(modulesRankedByLLM[0])
        }
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
        setLoading(true); // Start loading unranked modules
        setSelectedModule(null);
        setSelectedTab(0)
        setModules([]);

        const filters = {
            schools,
            departments: Object.values(departments).flat(),
            studyLevel,
            ectsRange,
            digitalScoreRange,
            languages,
            topicsOfInterest,
            excludedTopics,
            previousModules: previousModules.map((module) => module.id),
            studentText
        };

        const response = await fetchModules(filters, page); // Pass the page argument to fetchModules
        if (response) {
            setModules(response.modules);
            setSelectedModule(response.modules[0] || null);
            setTotalPages(response.totalPages);
            setLoading(false); // End loading for unranked modules
            if (studentText) {
                setModulesRankedByLLM([]);
                fetchRankedModules(filters, page); // Start fetching ranked modules in the background

            }
        } else {
            setLoading(false); // End loading if there was an error
        }
    };

    const fetchRankedModules = async (filters, page) => {
        setLoadingRankedModules(true); // Start loading ranked modules

        try {
            const response = await fetchModules(filters, page, true); // Add a flag or modify to fetch ranked modules
            if (response) {
                setModulesRankedByLLM(response.modulesRankedByLLM || []);
                if (selectedTab === 1) {
                    setSelectedModule(modulesRankedByLLM[0])
                }
            }
        } catch (error) {
            console.error('Error fetching ranked modules:', error);
        } finally {
            setLoadingRankedModules(false); // End loading for ranked modules
        }
    };


    const fetchModules = async (filters, page, ranked = false) => {  // Accept page and ranked as arguments
        try {
            const flattenedTopicsOfInterest = Object.values(filters.topicsOfInterest).flat();
            const flattenedExcludedTopics = Object.values(filters.excludedTopics).flat();

            const params = {
                ...filters,
                topicsOfInterest: flattenedTopicsOfInterest,
                excludedTopics: flattenedExcludedTopics,
                page: page,
                size: pageSize,
            };

            // If fetching ranked modules, add a query parameter or adjust the request as needed
            const url = ranked ? 'http://localhost:8080/modules-ranked' : 'http://localhost:8080/modules';
            const response = await axios.get(url, {params});
            return response.data;
        } catch (error) {
            console.error('Error fetching modules:', error);
        }
    };

    const handlePageChange = (event, value) => {
        setCurrentPage(value);
        handleRefresh(value); // Refresh data with the new page number
    };

    const handleClearFilters = (event) => {
        event.stopPropagation();
        setSchools([]);
        setDepartments({});
        setStudyLevel('');
        setEctsRange([1, 30]);
        setLanguages(languagesData);
        setTopicsOfInterest({});
        setExcludedTopics({});
        setPreviousModules([]);
        setDigitalScoreRange([0, 4])
    };


    const handleModuleClick = (module) => {
        setSelectedModule(module);
    };
    const renderModuleList = (modulesToRender) => {
        if (modulesToRender) {
            return modulesToRender.map((module) => (<ListItem
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
            </ListItem>));
        }
    };

    return <Container maxWidth="lg" sx={{mt: 4}}>
        <Box display="flex" justifyContent="left" mb={4}>
            <img src={logo} alt="TUM Logo" style={{width: '150px', height: 'auto'}}/>
            <Typography variant="h1" marginX={2} color={"#3070b3"}>
                Course Recommender
            </Typography>
        </Box>

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

        {showFilters && <Box paddingY={2}> <Accordion expanded={filtersExpanded} onChange={handleAccordionChange}>
            <AccordionSummary>
                <Box sx={{display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center'}}>
                    <Button>
                        {filtersExpanded ? 'Hide Filters' : 'Show Filters'}
                    </Button>
                    {filtersExpanded ? <Button
                        sx={{ml: 2}}
                        onClick={handleClearFilters}
                    >
                        Clear All Filters
                    </Button> : null}
                </Box>
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
                                maxWidth="100%"
                                alignItems="center"
                                gap={1}
                                sx={{
                                    '&::-webkit-scrollbar': {
                                        height: '8px',
                                    }, '&::-webkit-scrollbar-thumb': {
                                        backgroundColor: '#888', borderRadius: '4px',
                                    }, '&::-webkit-scrollbar-thumb:hover': {
                                        backgroundColor: '#555',
                                    },
                                }}
                            >
                                {organisationsData[school] && organisationsData[school].map((department) => (<Chip
                                    key={department}
                                    label={department.replace(/^Department\s*/, '')}
                                    onClick={() => handleDepartmentChange(school, department)}
                                    color={departments[school]?.includes(department) ? 'primary' : 'default'}
                                    variant={departments[school]?.includes(department) ? 'filled' : 'outlined'}
                                    sx={{cursor: 'pointer', whiteSpace: 'nowrap'}}
                                />))}
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
                    <Box display="flex" margin="normal" sx={{mb: 4, mr: 2}}>
                        {/* Language Preference on the Left */}
                        <Box width="25%">
                            <FormControl component="fieldset" fullWidth margin="normal" sx={{mb: 2, flex: 1}}>
                                <Typography component="legend">Language Preference</Typography>
                                <FormGroup>
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
                        </Box>

                        {/* Sliders on the Right in Two Rows */}
                        <Box sx={{flex: 1, ml: 2}}>
                            <Box my={2} sx={{mb: 4}}>
                                <Typography component="legend">ECTS Range (1-30)</Typography>
                                <Slider
                                    value={ectsRange}
                                    onChange={handleEctsRangeChange}
                                    valueLabelDisplay="auto"
                                    disableSwap={true}
                                    min={1}
                                    max={30}
                                />
                            </Box>
                            <Box my={2} sx={{mb: 4}}>
                                <Typography component="legend">Digital Score Range (0-3)</Typography>
                                <Slider
                                    value={digitalScoreRange}
                                    onChange={handleDigitalScoreRange}
                                    valueLabelDisplay="auto"
                                    disableSwap={true}
                                    min={1}
                                    max={3}
                                />
                            </Box>
                        </Box>
                    </Box>

                    <Typography component="legend">Topics</Typography>
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
        {showFilters && !loading && (
            <Tabs value={selectedTab} onChange={handleTabChange} centered>
                <Tab label="Modules 1"/>
                {modulesRankedByLLM && (
                    <Tab
                        label={
                            <Box display="flex" alignItems="center">
                                Modules 2
                                {loadingRankedModules && (
                                    <CircularProgress size={20} sx={{ml: 1}}/>
                                )}
                            </Box>
                        }
                    />
                )}
            </Tabs>
        )}
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
                            {selectedTab === 0 ? renderModuleList(modules) : renderModuleList(modulesRankedByLLM)}
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
