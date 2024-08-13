import React, {useState} from 'react';
import {
    Box,
    Button,
    Container,
    TextField,
    Typography,
    Card,
    CardContent,
    Grid
} from '@mui/material';
import axios from 'axios';
import {useNavigate} from "react-router-dom";

const StudyPreferencesForm = () => {
    const [preferences, setPreferences] = useState('');
    const [suggestedFilters, setSuggestedFilters] = useState({
        major: '',
        minor: '',
        studyLevel: '',
        school: '',
        departments: [],
        semester: null,
        ectsMin: 1,
        ectsMax: 30,
        topicsOfInterest: {},  // Object structure
        topicsToExclude: [],
        previousCourses: [],
        languages: [],
    });

    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();

        try {
            const response = await axios.post('http://localhost:8080/start-extraction', {
                text: preferences
            });

            if (response.data.success) {
                console.log(response.data.filters.topicsOfInterest)
                setSuggestedFilters(response.data.filters);
            } else {
                console.error('Extraction failed:', response.data.message);
            }
        } catch (error) {
            console.error('Error during extraction:', error);
        }
    };

    const handleContinue = () => {
        navigate("/", {state: suggestedFilters});  // Redirect to CourseRecommender with filters in state
    };

    return (
        <Container maxWidth="md" sx={{mt: 4, mb: 4}}>
            <Box
                component="form"
                onSubmit={handleSubmit}
                sx={{
                    backgroundColor: '#f5f5f5',
                    padding: 3,
                    borderRadius: 2,
                    boxShadow: 2
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
                    value={preferences}
                    onChange={(e) => setPreferences(e.target.value)}
                    sx={{mb: 2}}
                />
                <Button type="submit" variant="contained" color="primary">
                    Submit
                </Button>
            </Box>

            <Card sx={{mt: 4, boxShadow: 2}}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Suggested Filters
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={6}>
                            <Typography variant="body2"><strong>Major:</strong> {suggestedFilters.major}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2"><strong>Minor:</strong> {suggestedFilters.minor}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2"><strong>Study Level:</strong> {suggestedFilters.studyLevel}
                            </Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2"><strong>School:</strong> {suggestedFilters.school}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography
                                variant="body2"><strong>Departments:</strong> {suggestedFilters.departments.join(', ')}
                            </Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2"><strong>Semester:</strong> {suggestedFilters.semester}
                            </Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2"><strong>ECTS Min:</strong> {suggestedFilters.ectsMin}
                            </Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2"><strong>ECTS Max:</strong> {suggestedFilters.ectsMax}
                            </Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2">
                                <strong>Topics of Interest:</strong>
                                {Object.entries(suggestedFilters.topicsOfInterest).map(([topic, mappings]) => (
                                    <span key={topic}>{topic}: {mappings.join(', ')}; </span>
                                ))}
                            </Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2">
                                <strong>Topics of Interest:</strong>
                                {Object.entries(suggestedFilters.topicsToExclude).map(([topic, mappings]) => (
                                    <span key={topic}>{topic}: {mappings.join(', ')}; </span>
                                ))}
                            </Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography variant="body2"><strong>Previous
                                Courses:</strong> {suggestedFilters.previousCourses.join(", ")}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                            <Typography
                                variant="body2"><strong>Languages:</strong> {suggestedFilters.languages.join(", ")}
                            </Typography>
                        </Grid>
                    </Grid>
                    <Box sx={{mt: 2}}>
                        <Button variant="contained" color="primary" onClick={handleContinue}>
                            Continue
                        </Button>
                    </Box>
                </CardContent>
            </Card>
        </Container>
    );
};

export default StudyPreferencesForm;
