library(dplyr)
library(tidyr)
library(ggplot2)
library(readxl)

# Load merged TF-IDF
tfidf <- read_excel("C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/relative_frequencies/command_tokens/tf_idf/tf_idf.xlsx")

# Select only numeric TF-IDF columns for calculation
tfidf_rel <- tfidf %>%
  select(-game_id)  # drop non-numeric columns

# Average TF-IDF scores 
tfidf_avg <- tfidf_rel %>%
  group_by(name) %>%
  summarise(across(where(is.numeric), mean, na.rm = TRUE)) %>%
  ungroup()

# Pivot longer for plotting
tfidf_long <- tfidf_avg %>%
  pivot_longer(-name, names_to = "command", values_to = "tfidf")

# Pick top 20 commands by overall mean tf-idf
top_commands <- tfidf_long %>%
  group_by(command) %>%
  summarise(global_mean = mean(tfidf)) %>%
  arrange(desc(global_mean)) %>%
  slice_head(n = 30) %>%
  pull(command)

# Filter to top commands only
tfidf_long_top <- tfidf_long %>%
  filter(command %in% top_commands)

# Plot heatmap
ggplot(tfidf_long_top, aes(x = name, y = command, fill = tfidf)) +
  geom_tile() +
  scale_fill_gradient(low = "white", high = "#1B9E77FF") +
  theme_gray() +
  labs(title = "Top Commands by Game",
       x = "Game",
       y = "Command",
       fill = "TF-IDF score") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

