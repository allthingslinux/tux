-- Create the trigger function
CREATE OR REPLACE FUNCTION increment_case_number() RETURNS TRIGGER AS $$
DECLARE
    new_case_number INT;
BEGIN
    SELECT COALESCE(MAX(case_number), 0) + 1 INTO new_case_number
    FROM "Case"
    WHERE guild_id = NEW.guild_id;

    NEW.case_number = new_case_number;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
CREATE TRIGGER set_case_number
BEFORE INSERT ON "Case"
FOR EACH ROW
EXECUTE FUNCTION increment_case_number();
