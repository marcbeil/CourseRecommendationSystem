import React, {useEffect, useState} from 'react';
import {
    Box,
    Typography,
    Chip,
    Divider,
    Tooltip,
    useMediaQuery,
} from '@mui/material';
import axios from 'axios';
import {useTheme} from '@mui/material/styles';

// Import Material-UI icons
import SchoolIcon from '@mui/icons-material/School';
import BusinessIcon from '@mui/icons-material/Business';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import LanguageIcon from '@mui/icons-material/Language';
import CreditScoreIcon from '@mui/icons-material/CreditScore';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import DescriptionIcon from '@mui/icons-material/Description';
import ListIcon from '@mui/icons-material/List';
import LabelIcon from '@mui/icons-material/Label';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

const accentColor = '#3070b3'; // Your accent color

const ModuleDetail = ({selectedModule, topicsOfInterest}) => {
    const [prereqModuleList, setPrereqModuleList] = useState([]);

    const theme = useTheme();
    const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));

    useEffect(() => {
        // Fetch prerequisite modules whenever selectedModule changes
        if (selectedModule.prereqModules && selectedModule.prereqModules.length > 0) {
            fetchPrereqModuleList(selectedModule.prereqModules).then((modules) => {
                setPrereqModuleList(modules);
            });
        } else {
            setPrereqModuleList([]); // Clear the list if no prereqModules are available
        }
    }, [selectedModule]); // Depend on selectedModule to trigger reload on change

    const fetchPrereqModuleList = async (moduleIds) => {
        try {
            const response = await axios.get('http://localhost:8080/modules-by-id', {
                params: {
                    moduleIds,
                },
            });
            return response.data.modules || []; // Ensure an array is returned
        } catch (error) {
            console.error('Error fetching module details:', error);
            return []; // Return an empty array in case of error
        }
    };

    // Helper function to abbreviate long text
    const abbreviate = (text, maxLength = 50) => {
        if (text.length > maxLength) {
            return text.slice(0, maxLength - 3) + '...';
        }
        return text;
    };

    return (
        <Box>
            {/* Module Title */}
            <Typography variant="h5" gutterBottom sx={{color: accentColor}}>
                <strong>{selectedModule.title}</strong>
            </Typography>
            {selectedModule.reasoning && (
                <Box sx={{mb: 2}}>
                    <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                        <AutoAwesomeIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                        <Typography variant="body1">
                            <strong>AI Summary:</strong>
                        </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ml: 4}}>
                        {selectedModule.reasoning}
                    </Typography>
                </Box>
            )}

            {/* Two-Column Layout */}
            <Box
                sx={{
                    display: 'flex',
                    flexDirection: isSmallScreen ? 'column' : 'row',
                    justifyContent: 'space-between',
                    mb: 2,
                }}
            >
                {/* Left Column - Hierarchy */}
                <Box sx={{flex: 1, mr: isSmallScreen ? 0 : 2, mb: isSmallScreen ? 2 : 0}}>
                    <Typography variant="subtitle2" gutterBottom>
                        <strong>Hierarchy</strong>
                    </Typography>
                    <Box sx={{ml: 1}}>
                        <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                            <AccountBalanceIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                            <Typography variant="body2" color="textPrimary">
                                <strong>Chair:</strong> {selectedModule.chair}
                            </Typography>
                        </Box>
                        <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                            <BusinessIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                            <Typography variant="body2" color="textPrimary">
                                <strong>Department:</strong> {selectedModule.department}
                            </Typography>
                        </Box>
                        <Box sx={{display: 'flex', alignItems: 'center'}}>
                            <SchoolIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                            <Typography variant="body2" color="textPrimary">
                                <strong>School:</strong> {selectedModule.school}
                            </Typography>
                        </Box>
                    </Box>
                </Box>

                {/* Right Column - ECTS, Study Level, Language */}
                <Box sx={{flex: 1, ml: isSmallScreen ? 0 : 2}}>
                    <Typography variant="subtitle2" gutterBottom>
                        <strong>Module Details</strong>
                    </Typography>
                    <Box sx={{ml: 1}}>
                        <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                            <CreditScoreIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                            <Typography variant="body2">
                                <strong>ECTS:</strong> {selectedModule.ects}
                            </Typography>
                        </Box>
                        <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                            <MenuBookIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                            <Typography variant="body2">
                                <strong>Study Level:</strong> {selectedModule.studyLevel}
                            </Typography>
                        </Box>
                        <Box sx={{display: 'flex', alignItems: 'center'}}>
                            <LanguageIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                            <Typography variant="body2">
                                <strong>Language:</strong> {selectedModule.language}
                            </Typography>
                        </Box>
                    </Box>
                </Box>
            </Box>

            {/* Divider */}
            <Divider sx={{mb: 2}}/>

            {/* Description */}
            <Box sx={{mb: 2}}>
                <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                    <DescriptionIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                    <Typography variant="body1">
                        <strong>Description:</strong>
                    </Typography>
                </Box>
                <Typography variant="body2" sx={{ml: 4}}>
                    {selectedModule.description}
                </Typography>
            </Box>

            {/* Prerequisites */}
            {selectedModule.prereq && (
                <Box sx={{mb: 2}}>
                    <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                        <ListIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                        <Typography variant="body1">
                            <strong>Prerequisites:</strong>
                        </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ml: 4}}>
                        {selectedModule.prereq}
                    </Typography>
                </Box>
            )}

            {/* Prerequisite Modules */}
            {prereqModuleList.length > 0 && (
                <Box sx={{mb: 2}}>
                    <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                        <ListIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                        <Typography variant="body1">
                            <strong>Prerequisite Modules:</strong>
                        </Typography>
                    </Box>
                    <Box sx={{ml: 4}}>
                        {prereqModuleList.map((module, index) => (
                            <Typography key={index} variant="body2">
                                <strong>{module.id}:</strong> {module.title}
                            </Typography>
                        ))}
                    </Box>
                </Box>
            )}

            {/* Topics */}
            <Box sx={{mb: 2}}>
                <Box sx={{display: 'flex', alignItems: 'center', mb: 1}}>
                    <LabelIcon sx={{mr: 1, color: accentColor}} fontSize="small"/>
                    <Typography variant="body1">
                        <strong>Topics:</strong>
                    </Typography>
                </Box>
                <Box display="flex" flexWrap="wrap" sx={{ml: 4}}>
                    {selectedModule.topics.map((topic, index) => {
                        const isHighlighted = Object.values(topicsOfInterest).flat().includes(topic);

                        return (
                            <Tooltip key={index} title={topic}>
                                <Chip
                                    label={abbreviate(topic, 20)}
                                    variant="outlined"
                                    sx={{
                                        margin: '5px',
                                        borderColor: accentColor,
                                        color: accentColor,
                                        backgroundColor: isHighlighted ? '#ffeb3b' : 'inherit',
                                        fontWeight: isHighlighted ? 'bold' : 'normal',
                                    }}
                                />
                            </Tooltip>
                        );
                    })}
                </Box>
            </Box>
        </Box>
    );
};

export default ModuleDetail;
