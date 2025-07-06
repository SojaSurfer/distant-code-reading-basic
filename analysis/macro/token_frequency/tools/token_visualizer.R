# Load libraries
library(readxl)
library(dplyr)
library(tidyr)
library(ggplot2)
library(wordcloud)
library(RColorBrewer)

# Path to DTM
dtm_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/variable_tokens/document_term_matrix/DTM.xlsx"

# Read DTM
dtm <- read_excel(dtm_file)

# Summarize token frequencies (exclude metadata columns)
token_totals <- dtm %>%
  select(-game_id, -document) %>%
  summarise(across(everything(), sum)) %>%
  pivot_longer(cols = everything(), names_to = "token", values_to = "total_frequency") %>%
  arrange(desc(total_frequency)) %>%
  slice_head(n = 10)

# Bar chart
ggplot(token_totals, aes(x = reorder(token, total_frequency), y = total_frequency)) +
  geom_col(fill = "steelblue") +
  coord_flip() +
  labs(title = "Top 10 most frequent command_tokens",
       x = "Token",
       y = "Total frequency") +
  theme_minimal()

# Word cloud
# Top 100 tokens (or as many as available)
token_totals_all <- dtm %>%
  select(-game_id, -document) %>%
  summarise(across(everything(), sum)) %>%
  pivot_longer(cols = everything(), names_to = "token", values_to = "total_frequency") %>%
  filter(total_frequency > 0)

# Create word cloud
wordcloud(words = token_totals_all$token,
          freq = token_totals_all$total_frequency,
          min.freq = 1,                 
          max.words = 100,             
          colors = brewer.pal(8, "Dark2"),
          scale = c(4, 0.5),           # adjust text scaling
          random.order = FALSE) # for readability

# Create Pie chart
# Top 10 + combine the rest as "Other"
top_n <- 10
token_totals_pie <- token_totals_all %>%
  arrange(desc(total_frequency)) %>%
  mutate(token = as.character(token)) %>%
  mutate(token_grouped = if_else(row_number() <= top_n, token, "Other")) %>%
  group_by(token_grouped) %>%
  summarise(total = sum(total_frequency)) %>%
  ungroup() %>%
  arrange(desc(total)) %>% # descending order
  mutate(token_grouped = factor(token_grouped, levels = token_grouped)) 

# Pie chart
ggplot(token_totals_pie, aes(x = "", y = total, fill = token_grouped)) +
  geom_col(width = 1) +
  coord_polar(theta = "y") +
  labs(title = "Distribution of Variable Tokens (Top 10 + Other)", fill = "Token") +
  theme_void() +
  scale_fill_brewer(palette = "Set3")

