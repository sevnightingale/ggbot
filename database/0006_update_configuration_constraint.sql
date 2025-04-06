-- database/0006_update_configuration_constraint.sql
-- Update configurations table unique constraint to include config_name

-- Drop existing constraint
ALTER TABLE configurations
DROP CONSTRAINT IF EXISTS configurations_user_id_config_type_key;

-- Create new constraint that includes config_name
ALTER TABLE configurations
ADD CONSTRAINT configurations_user_id_config_type_name_key
UNIQUE (user_id, config_type, config_name);

-- Add comment explaining the constraint
COMMENT ON CONSTRAINT configurations_user_id_config_type_name_key 
ON configurations IS 'Ensures each user can have multiple configurations of the same type with different names';