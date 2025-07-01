library(readxl)
library(writexl)
library(dplyr)

# Path to your DTM file (absolute frequencies)
input_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/absolute_frequencies/operator_tokens/document_term_matrix/DTM.xlsx"

# Output file path for the summed relative frequencies
output_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/relative_frequencies/operator_tokens/relative_frequencies.xlsx"

# Read the DTM
dtm <- read_excel(input_file)

# Define metadata columns to exclude from summation
metadata_cols <- c("game_id", "document")  

# Select only token columns
token_cols <- setdiff(names(dtm), metadata_cols)
list(token_cols)

# Sum frequencies for each token across all documents
token_totals <- dtm %>%
  summarise(across(all_of(token_cols), sum, na.rm = TRUE))
list(token_totals)

# Calculate total sum of all tokens
total_all_tokens <- sum(token_totals)
list(total_all_tokens)

# Calculate relative frequency per token
token_rel_freq <- token_totals / total_all_tokens
list(token_rel_freq)

# Convert to a data frame with token names as column and one row of relative freq
token_rel_freq_df <- as.data.frame(token_rel_freq)

# Optionally, add a row name or ID to identify
token_rel_freq_df <- token_rel_freq_df %>%
  mutate(token = "relative_frequency") %>%
  select(token, everything())

# Save output
write_xlsx(token_rel_freq_df, output_file)

cat("Token totals and relative frequencies saved to:", output_file, "\n")

