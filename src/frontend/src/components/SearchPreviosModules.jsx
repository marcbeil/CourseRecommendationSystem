import React, {useState, useEffect} from 'react';
import {TextField, Box, List, ListItem, ListItemText, Typography, IconButton} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';

import axios from 'axios';

const SearchPreviousModules = ({previousModules, setPreviousModules}) => {
    const [moduleSearch, setModuleSearch] = useState('');
    const [recommendations, setRecommendations] = useState([]);

    const fetchRecommendations = async (query) => {
        try {
            const response = await axios.get('http://localhost:8080/search-modules', {
                params: {query}
            });
            setRecommendations(response.data.modules || []);
        } catch (error) {
            console.error('Error fetching module recommendations:', error);
        }
    };

    // Debounce function to limit API calls
    useEffect(() => {
        if (moduleSearch) {
            const debounceTimeout = setTimeout(() => {
                fetchRecommendations(moduleSearch);
            }, 300); // 300ms debounce time
            return () => clearTimeout(debounceTimeout);
        } else {
            setRecommendations([]); // Clear recommendations when input is empty
        }
    }, [moduleSearch]);

    const handleModuleSelect = (module) => {
        setPreviousModules(prev => [...prev, module]);
        setModuleSearch(''); // Clear search input after selection
        setRecommendations([]); // Clear recommendations after selection
    };

    const handleRemovePreviousModule = (index) => {
        setPreviousModules(prev => prev.filter((_, i) => i !== index));
    };

    return (
        <Box>
            <TextField
                label="Add Previous Modules by ID or Name"
                variant="outlined"
                fullWidth
                margin="normal"
                value={moduleSearch}
                onChange={(e) => setModuleSearch(e.target.value)}
            />
            <List>
                {recommendations.map((module, index) => (
                    <ListItem
                        button
                        key={index}
                        onClick={() => handleModuleSelect(module)}
                    >
                        <ListItemText primary={`${module.id} - ${module.title}`}/>
                    </ListItem>
                ))}
            </List>


            <List>
                {previousModules.map((module, index) => (
                    <ListItem key={index}
                              secondaryAction={
                                  <IconButton edge="end" aria-label="delete"
                                              onClick={() => handleRemovePreviousModule(index)}>
                                      <CloseIcon/>
                                  </IconButton>
                              }
                    >
                        <ListItemText primary={`${module.id} - ${module.title}`}/>
                    </ListItem>
                ))}
            </List>

        </Box>
    );
};

export default SearchPreviousModules;
