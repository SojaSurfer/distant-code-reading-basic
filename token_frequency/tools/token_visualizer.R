# Load libraries
library(readxl)
library(dplyr)
library(tidyr)
library(ggplot2)

# Path to DTM
dtm_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/command_tokens/document_term_matrix/DTM.xlsx"

# Read DTM
dtm <- read_excel(dtm_file)

# Summarize token frequencies (exclude metadata columns)
token_totals <- dtm %>%
  select(-game_id, -document) %>%
  summarise(across(everything(), sum)) %>%
  pivot_longer(cols = everything(), names_to = "token", values_to = "total_frequency") %>%
  arrange(desc(total_frequency)) %>%
  slice_head(n = 10)

# Plot
ggplot(token_totals, aes(x = reorder(token, total_frequency), y = total_frequency)) +
  geom_col(fill = "steelblue") +
  coord_flip() +
  labs(title = "Top 10 most frequent command_tokens",
       x = "Token",
       y = "Total frequency") +
  theme_minimal()
