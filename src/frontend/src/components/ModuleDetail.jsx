import {Box, Chip, Paper, Typography} from "@mui/material";
import React, {useEffect, useState} from "react";
import axios from "axios";

const ModuleDetail = ({selectedModule, topicsOfInterest}) => {
    const [prereqModuleList, setPrereqModuleList] = useState([]);

    useEffect(() => {
        // Fetch prerequisite modules whenever selectedModule changes
        if (selectedModule.prereqModules) {
            fetchPrereqModuleList(selectedModule.prereqModules).then(modules => {
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
                    moduleIds
                },
            });
            return response.data.modules || [];  // Ensure an array is returned
        } catch (error) {
            console.error('Error fetching module details:', error);
            return [];  // Return an empty array in case of error
        }
    };

    return (<Box>
        <Typography variant="h5" gutterBottom>
            {selectedModule.title}
        </Typography>
        {selectedModule.reasoning && <Typography variant="body1" gutterBottom>
            <strong>AI Summary:</strong> {selectedModule.reasoning}
        </Typography>}
        <Typography variant="body1" gutterBottom>
            <strong>Description</strong> {selectedModule.description}
        </Typography>
        <Typography variant="body2" gutterBottom>
            <strong>Prerequisites:</strong> {selectedModule.prereq}
        </Typography>
        <Typography variant="body2" gutterBottom>
            <strong>Module Prerequisites:</strong>
        </Typography>
        <Box marginLeft={4} marginBlockEnd={3}>
            {prereqModuleList.length > 0 ? (prereqModuleList.map((module, index) => (
                <Typography key={index} variant="body2">
                    <strong>{module.id} </strong>{module.title}
                </Typography>))) : (selectedModule.prereqModules.map((prereqId, index) => (
                <Typography key={index} variant="body2">
                    {prereqId}
                </Typography>)))}
        </Box>
        <Typography variant="body2" gutterBottom>
            <strong>Study Level:</strong> {selectedModule.studyLevel}
        </Typography>
        <Typography variant="body2" gutterBottom>
            <strong>Language:</strong> {selectedModule.language}
        </Typography>
        <Typography variant="body2" gutterBottom>
            <strong>Chair:</strong> {selectedModule.chair}
        </Typography>
        <Typography variant="body2" gutterBottom>
            <strong>Department:</strong> {selectedModule.department}
        </Typography>
        <Typography variant="body2" gutterBottom>
            <strong>School:</strong> {selectedModule.school}
        </Typography>
        <Box display="flex" flexWrap="wrap" mb={2}>
            {selectedModule.topics.map((topic, index) => {
                const isHighlighted = Object.values(topicsOfInterest).flat().includes(topic);

                return (<Chip
                    key={index}
                    label={topic}
                    color={isHighlighted ? "secondary" : "primary"}
                    variant="outlined"
                    style={{
                        margin: '5px',
                        backgroundColor: isHighlighted ? '#ffeb3b' : 'inherit',
                        fontWeight: isHighlighted ? 'bold' : 'normal',
                    }}
                />);
            })}
        </Box>
    </Box>);
};

export default ModuleDetail;
