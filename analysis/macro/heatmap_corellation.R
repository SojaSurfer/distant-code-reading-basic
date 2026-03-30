library(dplyr)
library(tidyr)
library(ggplot2)
library(readxl)
library(writexl)

# Load merged TF-IDF
tfidf <- read_excel("C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/relative_frequencies/command_tokens/tf_idf/tf_idf.xlsx")

# Keep only numeric TF-IDF columns
tfidf_rel <- tfidf %>%
  select(-game_id)  # drop non-numeric column(s)

# Average TF-IDF scores per command (if needed)
tfidf_avg <- tfidf_rel %>%
  group_by(name) %>%
  summarise(across(where(is.numeric), mean, na.rm = TRUE)) %>%
  ungroup()

# Make it into a matrix (commands as columns)
mat <- as.matrix(select(tfidf_avg, -name))
rownames(mat) <- tfidf_avg$name

# Compute correlation between commands
corr_matrix <- cor(mat, use = "pairwise.complete.obs", method = "pearson")

# Convert correlation matrix to long format
corr_long <- as.data.frame(as.table(corr_matrix))
colnames(corr_long) <- c("command1", "command2", "correlation")

# Optionally, limit to top N commands by mean TF-IDF
top_commands <- tfidf_avg %>%
  select(-name) %>%
  summarise(across(everything(), mean, na.rm = TRUE)) %>%
  pivot_longer(cols = everything(), names_to = "command", values_to = "mean_tfidf") %>%
  arrange(desc(mean_tfidf)) %>%
  slice_head(n = 55) %>%
  pull(command)

corr_long <- corr_long %>%
  filter(command1 %in% top_commands & command2 %in% top_commands)

# Plot correlation heatmap
ggplot(corr_long, aes(x = command1, y = command2, fill = correlation)) +
  geom_tile() +
  scale_fill_gradient2(low = "#1B9E77FF", mid = "white", high = "#D95F02FF", midpoint = 0) +
  theme_gray() +
  labs(title = "Command-to-Command Correlation Heatmap",
       x = "Command",
       y = "Command",
       fill = "Correlation") +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))

# Save matrix
all_cor_matrix <- corr_matrix

# Convert to data frame
all_cor_df <- data.frame(Command = rownames(corr_matrix), corr_matrix)

# Save as xlsx
write_xlsx(all_cor_df, "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/visuals/command_correlation.xlsx")