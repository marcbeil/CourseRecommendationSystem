import {Box, Chip, Paper, Typography, TextField} from "@mui/material";
import React from "react";

const TopicChips = ({topics, setTopics, type, fetchTopicMappings}) => {

    const handleAddTopic = async (event) => {
        if (event.key === 'Enter' && event.target.value) {
            const topic = event.target.value;
            const topicMappings = await fetchTopicMappings(topic);  // Wait for the promise to resolve
            if (Array.isArray(topicMappings)) {  // Ensure the result is an array
                setTopics(prev => ({
                    ...prev,
                    [topic]: topicMappings
                }));
            } else {
                console.error('Received topic mappings is not an array:', topicMappings);
            }
            event.target.value = '';
        }
    };

    const handleDeleteTopic = (enteredTopic, mappingToDelete) => {
        setTopics(prev => {
            const newMappings = prev[enteredTopic].filter(mapping => mapping !== mappingToDelete);

            if (newMappings.length === 0) {
                const newTopics = {...prev};
                delete newTopics[enteredTopic];
                return newTopics;
            }

            return {
                ...prev,
                [enteredTopic]: newMappings
            };
        });
    };

    return (
        <Box my={2}>
            <TextField
                label={`Add ${type === 'interest' ? 'Topic of Interest' : 'Excluded Topic'}`}
                variant="outlined"
                fullWidth
                margin="normal"
                onKeyDown={handleAddTopic}
                placeholder="Press Enter to add"
            />
            {Object.entries(topics).map(([enteredTopic, mappings], index) => (
                <Box key={index} mb={2}>
                    <Paper
                        elevation={1}
                        style={{
                            display: 'inline-block',
                            padding: '10px',
                            borderRadius: '16px',
                            backgroundColor: type === 'interest' ? '#e0f7fa' : '#fae0e0',
                        }}
                    >
                        <Typography variant="subtitle1" gutterBottom>
                            {enteredTopic}
                        </Typography>
                        <Box display="flex" flexWrap="wrap">
                            {mappings.map((mapping, idx) => (
                                <Chip
                                    key={idx}
                                    label={mapping}
                                    onDelete={() => handleDeleteTopic(enteredTopic, mapping)}
                                    color="primary"
                                    variant="outlined"
                                    style={{margin: '5px'}}
                                />
                            ))}
                        </Box>
                    </Paper>
                </Box>
            ))}
        </Box>
    );
};

export default TopicChips;
